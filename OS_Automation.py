import speech_recognition as sr
import os
import platform
import time
import pyttsx3
import subprocess
import pyautogui

def get_desktop_path():
    """Gets the path to the user's desktop."""
    if platform.system() == "Windows":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    else:
        return None

def create_folder(folder_name):
    """Creates a folder on the desktop."""
    desktop_path = get_desktop_path()
    if desktop_path:
        folder_path = os.path.join(desktop_path, folder_name)
        try:
            os.makedirs(folder_path)
            return True, folder_path
        except FileExistsError:
            return False, "Folder already exists."
        except Exception as e:
            return False, f"An error occurred: {e}"
    else:
        return False, "Unsupported operating system."

def speak(text):
    """Speaks the given text."""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def sleep_pc():
    """Puts the PC to sleep."""
    if platform.system() == "Windows":
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    elif platform.system() == "Linux":
        subprocess.run(["systemctl", "suspend"])
    elif platform.system() == "Darwin":
        subprocess.run(["pmset", "sleepnow"])
    else:
        speak("Sleep command not supported on this operating system.")

def lock_pc():
    """Locks the PC."""
    if platform.system() == "Windows":
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    elif platform.system() == "Linux":
        subprocess.run(["gnome-screensaver-command", "--lock"])
    elif platform.system() == "Darwin":
        subprocess.run(["/System/Library/CoreServices/Menu\ Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
    else:
        speak("Lock command not supported on this operating system.")

def open_application(application_name):
    """Opens the specified application."""
    try:
        if application_name == "vs code":
            if platform.system() == "Windows":
                subprocess.Popen(["D:\Microsoft VS Code\Code.exe"]) #OS_AUTOMATION Enter your file location of vs code
            elif platform.system() == "Linux":
                subprocess.Popen(["code"])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", "Visual Studio Code"])
        elif application_name == "notepad":
            if platform.system() == "Windows":
                subprocess.Popen(["C:\\Windows\\System32\\notepad.exe"]) #OS_AUTOMATION Enter your file location of Notepad
            elif platform.system() == "Linux":
                subprocess.Popen(["gedit"])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", "TextEdit"])
        elif application_name == "this pc":
            if platform.system() == "Windows":
                subprocess.Popen(["explorer.exe", "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}"])
            else:
                speak("This PC command only supported on windows")
        elif application_name == "recycle bin":
            if platform.system() == "Windows":
                subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
            else:
                speak("Recycle bin command only supported on windows")
        elif application_name == "file explorer":
            if platform.system() == "Windows":
                subprocess.Popen(["explorer.exe"])
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", os.path.expanduser("~")])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", os.path.expanduser("~")])
        else:
            speak(f"Application '{application_name}' not recognized.")
    except FileNotFoundError:
        speak(f"Application '{application_name}' not found.")
    except Exception as e:
        speak(f"An error occurred while opening '{application_name}': {e}")

def close_tabs(number_of_tabs):
    """Closes the specified number of tabs."""
    try:
        number_of_tabs = int(number_of_tabs)
        for _ in range(number_of_tabs):
            pyautogui.hotkey('ctrl', 'w')
        speak(f"{number_of_tabs} tabs closed.")
    except ValueError:
        speak("Invalid number of tabs.")
    except Exception as e:
        speak(f"An error occurred while closing tabs: {e}")

def voice_assistant():
    """Voice assistant that handles various commands."""
    recognizer = sr.Recognizer()

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                speak("Listening...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)

            print("Recognizing...")
            speak("Recognizing...")
            query = recognizer.recognize_google(audio).lower()
            print(f"User said: {query}")

            if "create new folder" in query:
                folder_name = query.replace("create new folder", "").strip()
                if not folder_name:
                    folder_name = "New Folder"
                success, message = create_folder(folder_name)
                if success:
                    print(f"Folder '{folder_name}' created successfully.")
                    print(f"Folder path: {message}")
                    speak("New folder created.")
                else:
                    print(message)
                    speak(message)
            elif "sleep pc" in query:
                sleep_pc()
                speak("Going to sleep.")
            elif "lock pc" in query:
                lock_pc()
                speak("Locking the PC.")
            elif "open" in query:
                application_name = query.replace("open", "").strip()
                open_application(application_name)
            elif "close tabs" in query:
                try:
                    tabs_to_close = query.split("close tabs")[1].strip()
                    close_tabs(tabs_to_close)
                except IndexError:
                    speak("How many tabs do you want to close?")
                except Exception as e:
                    speak(f"An error occurred: {e}")
            else:
                print("Command not recognized.")
                speak("Command not recognized.")

        except sr.UnknownValueError:
            print("Could not understand audio.")
            speak("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            speak(f"Could not request results; {e}")
        except sr.WaitTimeoutError:
            print("Listening timed out. Listening again.")
            speak("Listening timed out. Listening again.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            speak(f"An unexpected error occurred: {e}")

        time.sleep(1)

if __name__ == "__main__":
    voice_assistant()