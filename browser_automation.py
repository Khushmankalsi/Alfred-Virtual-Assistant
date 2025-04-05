import speech_recognition as sr
import pyttsx3
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import json
from selenium.common.exceptions import ElementNotInteractableException, StaleElementReferenceException, TimeoutException, NoSuchElementException

load_dotenv()
# Initialize the speech recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
command_received = None

# Configure Gemini API
GEMINI_API_KEY = os.getenv("API_KEY")  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen for voice commands in a separate thread
def listen_thread():
    global command_received
    while True:
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio)
                print(f"You said: {command}")
                command_received = command.lower()
            except sr.UnknownValueError:
                print("Sorry, I did not understand that.")
            except sr.RequestError:
                print("Could not request results from Google Speech Recognition service.")
        time.sleep(0.1)  # Small pause to prevent CPU overuse

# Function to process natural language with Gemini AI
def process_with_gemini(command):
    prompt = f"""
    I am a voice-controlled browser assistant. Parse the following command and return a JSON object with:
    1. "intent": The primary action being requested (open_website, search, scroll, navigate, click, etc.)
    2. "target": The target website, search query, or element
    3. "parameters": Any additional parameters
    
    Command: "{command}"
    
    For website requests like "open YouTube", set:
    - intent: "open_website"
    - target: "youtube.com"
    
    For scrolling commands, set:
    - intent: "scroll"
    - target: "down" for scrolling downward
    - target: "up" for scrolling upward
    - target: "top" for "scroll to top"
    - target: "bottom" for "scroll to bottom"
    
    For search requests, extract the search query.
    
    For click commands like "click on X" or "open the link about Y", set:
    - intent: "click"
    - target: the text or description of what to click on
    
    Return ONLY the JSON object with no additional text.
    """
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Extract the JSON object if it's wrapped in code blocks
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        
        # Parse the JSON
        parsed_result = json.loads(result)
        
        # Debug the parsed result
        print(f"Parsed result: {parsed_result}")
        
        # Handle common website names directly to avoid search confusion
        if parsed_result["intent"] == "open_website":
            website_map = {
                "youtube": "youtube.com",
                "google": "google.com",
                "facebook": "facebook.com",
                "twitter": "twitter.com",
                "instagram": "instagram.com",
                "linkedin": "linkedin.com",
                "reddit": "reddit.com",
                "amazon": "amazon.com",
                "netflix": "netflix.com"
            }
            
            # Check if target is a simple website name that should be mapped
            for simple_name, domain in website_map.items():
                if simple_name in parsed_result["target"].lower():
                    parsed_result["target"] = domain
                    break
        
        # Fix common scrolling command issues
        if parsed_result["intent"] == "scroll":
            scrolling_targets = ["scroll_start", "scroll_stop", "scroll_top", "scroll_bottom", 
                                "start_scrolling", "stop_scrolling", "scroll_up", "scroll_down",
                                "scrolling_start", "scrolling_stop"]
            
            if parsed_result["target"] in scrolling_targets:
                # Map to expected targets
                if "start" in parsed_result["target"] or "down" in parsed_result["target"]:
                    parsed_result["target"] = "down"
                elif "stop" in parsed_result["target"]:
                    parsed_result["target"] = "stop"
                elif "top" in parsed_result["target"]:
                    parsed_result["target"] = "top"
                elif "bottom" in parsed_result["target"]:
                    parsed_result["target"] = "bottom"
                elif "up" in parsed_result["target"]:
                    parsed_result["target"] = "up"
        
        # Handle click intents better - extract anything that could be click-related
        if "click" in command.lower() or "open" in command.lower() or "select" in command.lower() or "choose" in command.lower():
            if parsed_result["intent"] not in ["click", "open_website"]:
                # Try to extract what they want to click on
                text_to_click = command.lower()
                for prefix in ["click on ", "click ", "open ", "select ", "choose "]:
                    if prefix in text_to_click:
                        text_to_click = text_to_click.split(prefix, 1)[1]
                        parsed_result["intent"] = "click"
                        parsed_result["target"] = text_to_click
                        break
                    
        return parsed_result
    except Exception as e:
        print(f"Error processing with Gemini: {e}")
        return {"intent": "unknown", "target": None, "parameters": {}}

# Function to perform a fixed scroll
def fixed_scroll(driver, direction="down", scroll_amount=1000):
    try:
        if direction == "down":
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            speak(f"Scrolling down.")
        elif direction == "up":
            driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
            speak(f"Scrolling up.")
        elif direction == "top":
            driver.execute_script("window.scrollTo(0, 0);")
            speak("Scrolled to top.")
        elif direction == "bottom":
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            speak("Scrolled to bottom.")
        
        return True
    except Exception as e:
        print(f"Error scrolling: {e}")
        speak("Error during scrolling.")
        return False

# Function to open a website
def open_website(driver, website):
    # Check if the website already includes http:// or https://
    if not website.startswith(('http://', 'https://')):
        # Check if it's a domain name
        if '.' in website and ' ' not in website:
            url = 'https://' + website
        else:
            # Add .com if it appears to be a simple website name
            if ' ' not in website:
                url = 'https://' + website + '.com'
            else:
                # It's not a URL, search for it on Bing
                url = f"https://www.bing.com/search?q={website.replace(' ', '+')}"
    else:
        url = website
    
    try:
        print(f"Opening URL: {url}")
        driver.get(url)
        speak(f"Opening {website}")
        return True
    except Exception as e:
        speak(f"Error opening {website}")
        print(f"Error: {e}")
        return False

# Function to perform search on current website with improved error handling
def perform_search(driver, query):
    try:
        # First, try Google's search if we're on Google
        if "google.com" in driver.current_url:
            try:
                # Direct approach for Google search
                search_box = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.NAME, "q"))
                )
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                speak(f"Searching for {query} on Google")
                return True
            except Exception as e:
                print(f"Google-specific search failed: {e}")
                # Fall through to generic approach
        
        # Try YouTube's search if we're on YouTube
        if "youtube.com" in driver.current_url:
            try:
                # Direct approach for YouTube search
                search_box = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.NAME, "search_query"))
                )
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                speak(f"Searching for {query} on YouTube")
                return True
            except Exception as e:
                print(f"YouTube-specific search failed: {e}")
                # Fall through to generic approach
                
        # General approach - try multiple common search box identifiers with WebDriverWait
        search_selectors = [
            (By.XPATH, "//input[@type='search']"),
            (By.XPATH, "//input[@name='q']"),
            (By.XPATH, "//input[@name='search']"),
            (By.XPATH, "//input[contains(@placeholder, 'search') or contains(@placeholder, 'Search')]"),
            (By.XPATH, "//input[contains(@aria-label, 'search') or contains(@aria-label, 'Search')]"),
            (By.XPATH, "//input[contains(@class, 'search') or contains(@id, 'search')]"),
            (By.CSS_SELECTOR, "input[type='search']"),
            (By.CSS_SELECTOR, "input.search"),
            (By.CSS_SELECTOR, "input#search")
        ]
        
        for selector_type, selector in search_selectors:
            try:
                print(f"Trying selector: {selector_type} = {selector}")
                search_box = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((selector_type, selector))
                )
                # We found a search box, let's use it
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                speak(f"Searching for {query}")
                return True
            except (TimeoutException, ElementNotInteractableException, StaleElementReferenceException) as e:
                print(f"Selector {selector} failed: {e}")
                continue  # Try the next selector
        
        # If no search box was found or usable, fallback to direct Bing search
        print("No usable search box found, falling back to Bing search")
        driver.get(f"https://www.bing.com/search?q={query.replace(' ', '+')}")
        speak(f"Searching for {query} on Bing")
        return True
            
    except Exception as e:
        speak(f"Error performing search")
        print(f"Error: {e}")
        # Fallback to Bing search on error
        try:
            driver.get(f"https://www.bing.com/search?q={query.replace(' ', '+')}")
            speak(f"Searching for {query} on Bing")
            return True
        except Exception as e2:
            print(f"Fallback search also failed: {e2}")
            return False

# Enhanced function to find and list all clickable elements with their text for debugging
def list_clickable_elements(driver):
    try:
        print("Scanning page for clickable elements...")
        
        # Find all potential clickable elements
        elements = driver.find_elements(By.XPATH, "//a | //button | //input[@type='button'] | //input[@type='submit'] | //*[@role='button']")
        
        # Print count of elements found
        print(f"Found {len(elements)} potentially clickable elements")
        
        # Print details of elements with text or title
        count = 1
        for element in elements:
            try:
                text = element.text.strip() if element.text else ""
                title = element.get_attribute("title") or ""
                aria_label = element.get_attribute("aria-label") or ""
                href = element.get_attribute("href") or ""
                
                # Only print elements with some identifiable text
                if text or title or aria_label:
                    print(f"Element {count}: Text='{text}', Title='{title}', Aria-Label='{aria_label}', Href='{href}'")
                    count += 1
                    
            except StaleElementReferenceException:
                # Element might have changed since we got the list
                continue
                
        return True
    except Exception as e:
        print(f"Error listing clickable elements: {e}")
        return False

# Enhanced function to click on a link or element containing text
def click_element_with_text(driver, text):
    try:
        # Normalize the search text
        text = text.lower().strip()
        print(f"Looking for element containing: '{text}'")
        
        # First, try exact matches with these specific strategies for search results
        search_result_strategies = []
        
        if "google.com" in driver.current_url:
            # Google-specific search result selectors
            search_result_strategies = [
                f"//h3[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]/ancestor::a",
                f"//div[contains(@class, 'g')]//a[contains(., '{text}')]",
                f"//div[contains(@class, 'yuRUbf')]/a[contains(., '{text}')]"
            ]
        elif "bing.com" in driver.current_url:
            # Bing-specific search result selectors
            search_result_strategies = [
                f"//h2[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]/ancestor::a",
                f"//li[contains(@class, 'b_algo')]//a[contains(., '{text}')]"
            ]
        
        # Try site-specific selectors first if applicable
        for xpath in search_result_strategies:
            try:
                print(f"Trying site-specific selector: {xpath}")
                element = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)  # Small pause to let the page settle
                element.click()
                speak(f"Clicked on {text}")
                return True
            except (TimeoutException, ElementNotInteractableException, StaleElementReferenceException) as e:
                print(f"Site-specific XPath {xpath} failed: {e}")
                continue
        
        # If site-specific strategies didn't work, try these generic strategies
        generic_strategies = [
            # Start with exact text matches, case-insensitive
            f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            
            # Try attribute matches
            f"//*[contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            f"//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            f"//a[contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            
            # Try clicking anything with alt text (like images)
            f"//*[contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
            
            # Try parent/child relationships
            f"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]/ancestor::a",
            f"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]/ancestor::button"
        ]
        
        for xpath in generic_strategies:
            try:
                print(f"Trying generic strategy: {xpath}")
                elements = driver.find_elements(By.XPATH, xpath)
                print(f"Found {len(elements)} matching elements")
                
                # First, try elements that are directly visible
                for element in elements:
                    try:
                        if element.is_displayed():
                            # Scroll element into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.2)  # Small pause to let the page settle
                            element.click()
                            speak(f"Clicked on {text}")
                            return True
                    except (ElementNotInteractableException, StaleElementReferenceException) as e:
                        print(f"Element interaction failed: {e}")
                        continue
            except Exception as e:
                print(f"XPath {xpath} failed: {e}")
                continue
        
        # If we still haven't found anything, try a more lenient approach with partial words
        words = text.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 3:  # Only use words that are not too short
                    try:
                        xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]"
                        print(f"Trying with partial word: {word}")
                        elements = driver.find_elements(By.XPATH, xpath)
                        
                        for element in elements:
                            try:
                                if element.is_displayed():
                                    # Check if the element is clickable
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(0.2)
                                    element_text = element.text.strip() if element.text else ""
                                    print(f"Found element with text: '{element_text}'")
                                    element.click()
                                    speak(f"Clicked on element containing {word}")
                                    return True
                            except (ElementNotInteractableException, StaleElementReferenceException) as e:
                                print(f"Element interaction failed: {e}")
                                continue
                    except Exception as e:
                        print(f"Word search failed for '{word}': {e}")
                        continue
        
        # If we reached here, try to list all available clickable elements for debugging
        list_clickable_elements(driver)
        speak(f"Could not find clickable element containing {text}")
        return False
        
    except Exception as e:
        speak(f"Error clicking element")
        print(f"Error: {e}")
        return False

# Function to click on a result number (1st, 2nd, 3rd result)
def click_numbered_result(driver, number_text):
    try:
        # Convert text like "first", "second", "third" to numbers
        number_mapping = {
            "first": 1, "1st": 1, "one": 1,
            "second": 2, "2nd": 2, "two": 2,
            "third": 3, "3rd": 3, "three": 3,
            "fourth": 4, "4th": 4, "four": 4,
            "fifth": 5, "5th": 5, "five": 5
        }
        
        # Extract the number
        number = None
        for key, value in number_mapping.items():
            if key in number_text.lower():
                number = value
                break
                
        # Try to extract a direct number
        if not number:
            match = re.search(r'(\d+)', number_text)
            if match:
                number = int(match.group(1))
        
        if not number:
            speak("I couldn't determine which result number to click.")
            return False
            
        print(f"Trying to click on result number {number}")
        
        # Handle different search engines differently
        if "google.com" in driver.current_url:
            # For Google
            xpath = f"(//div[@class='g']//a)[{number}]"
            backup_xpath = f"(//h3/parent::a)[{number}]"
            
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                element.click()
                speak(f"Clicked on result number {number}")
                return True
            except Exception:
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, backup_xpath))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.2)
                    element.click()
                    speak(f"Clicked on result number {number}")
                    return True
                except Exception as e:
                    print(f"Failed to click Google result {number}: {e}")
        
        elif "bing.com" in driver.current_url:
            # For Bing
            xpath = f"(//li[@class='b_algo']//h2/a)[{number}]"
            
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                element.click()
                speak(f"Clicked on result number {number}")
                return True
            except Exception as e:
                print(f"Failed to click Bing result {number}: {e}")
                
        elif "youtube.com" in driver.current_url:
            # For YouTube
            xpath = f"(//ytd-video-renderer//a[@id='thumbnail'])[{number}]"
            
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                element.click()
                speak(f"Clicked on video number {number}")
                return True
            except Exception as e:
                print(f"Failed to click YouTube video {number}: {e}")
        
        # Generic approach for other sites - try to find the nth link
        xpath = f"(//a)[{number}]"
        try:
            element = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)
            element.click()
            speak(f"Clicked on link number {number}")
            return True
        except Exception as e:
            print(f"Failed to click generic link {number}: {e}")
            speak(f"Could not find result number {number}")
            return False
            
    except Exception as e:
        speak(f"Error clicking numbered result")
        print(f"Error: {e}")
        return False
        
# Main function to handle voice commands and control the browser
def voice_controlled_browser():
    global command_received
    # Start the listening thread
    listen_thread_instance = threading.Thread(target=listen_thread, daemon=True)
    listen_thread_instance.start()
    
    # Set up the Selenium WebDriver with options
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(executable_path=os.getenv('EDGE_WEBDRIVER_PATH'))  # Update the path
    driver = webdriver.Edge(service=service, options=options)
    
    # Open a blank page to start
    driver.get("about:blank")
    speak("Enhanced voice-controlled browser is ready. What would you like to do?")
    
    # Define default scroll amount (can be adjusted based on user preference)
    scroll_amount = 300
    
    while True:
        if command_received:
            # Process the command with Gemini API
            parsed_command = process_with_gemini(command_received)
            print(f"Parsed command: {parsed_command}")
            
            intent = parsed_command.get("intent", "unknown")
            target = parsed_command.get("target", "")
            parameters = parsed_command.get("parameters", {})
            
            # Handle different intents
            if intent == "open_website":
                open_website(driver, target)
                
            elif intent == "search":
                perform_search(driver, target)
                
            elif intent == "scroll":
                if target == "down":
                    fixed_scroll(driver, "down", scroll_amount)
                elif target == "up":
                    fixed_scroll(driver, "up", scroll_amount)
                elif target == "top":
                    fixed_scroll(driver, "top")
                elif target == "bottom":
                    fixed_scroll(driver, "bottom")
                    
            elif intent == "navigate":
                if target == "back":
                    driver.back()
                    speak("Going back.")
                elif target == "forward":
                    driver.forward()
                    speak("Going forward.")
                elif target == "refresh":
                    driver.refresh()
                    speak("Refreshing page.")
                    
            elif intent == "click":
                # Check if the target references a numbered result
                numbered_terms = ["first", "second", "third", "fourth", "fifth", 
                                 "1st", "2nd", "3rd", "4th", "5th",
                                 "result number", "link number", "number"]
                                 
                is_numbered = any(term in target.lower() for term in numbered_terms) or re.search(r'\d+', target)
                
                if is_numbered:
                    click_numbered_result(driver, target)
                else:
                    click_element_with_text(driver, target)
                
            elif intent == "exit" or intent == "quit":
                speak("Exiting the browser.")
                driver.quit()
                break
                
            elif intent == "list" and "links" in target:
                # Diagnostic command to list all clickable elements
                list_clickable_elements(driver)
                speak("Listed all clickable elements in the console.")
                
            elif intent == "unknown":
                speak("I'm not sure how to handle that command. Please try again.")
                
            command_received = None
        
        time.sleep(0.1)  # Small pause to prevent CPU overuse

if __name__ == "__main__":
    speak("Enhanced voice-controlled browser automation is starting.")
    voice_controlled_browser()
