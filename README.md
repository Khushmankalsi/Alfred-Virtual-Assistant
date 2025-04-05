# Alfred:- A Voice-Controlled Intelligent Assistant

## Project Mini Description

This project is a comprehensive voice-controlled intelligent assistant that integrates web browsing automation, file management, and system control. It leverages Google's Gemini AI for natural language processing, enabling users to interact with their computer using voice commands.

## Features

* **Voice Control:**
    * Utilizes `speech_recognition` for accurate voice input.
    * Provides clear text-to-speech output using `pyttsx3`.
    * Implements continuous listening in a background thread for seamless interaction.
* **Web Browsing Automation:**
    * Automates web browsing tasks with `selenium` (Edge browser).
    * Supports opening websites, performing searches, scrolling, navigating, and clicking elements.
    * Handles numbered search results and links effectively.
    * Includes robust error handling for web-related operations.
* **Gemini AI Integration:**
    * Leverages Google's Gemini API for advanced natural language processing.
    * Parses voice commands into structured JSON objects, extracting intent and target.
    * Enables understanding of complex voice instructions.
* **File Management:**
    * Creates folders on the desktop.
    * Opens drives and locations in Windows Explorer.
    * Deletes files and folders based on voice commands.
* **System Control:**
    * Locks the PC.
    * Puts the PC to sleep.
* **Error Handling:**
    * Implements `try-except` blocks to handle various exceptions gracefully.
    * Provides informative error messages to the user.
* **Modular Design:**
    * Code is organized into well-defined functions for clarity and maintainability.
    * Code is commented to explain functionality.
* **User Friendly:**
    * Designed to be very easy to use through simple voice commands.

## Prerequisites

* Python 3.x installed.
* Required Python libraries: `speech_recognition`, `pyttsx3`, `selenium`, `google-generativeai`. You can install them using pip:

    ```bash
    pip install SpeechRecognition pyttsx3 selenium google-generativeai
    ```

* Microsoft Edge browser and the corresponding WebDriver installed and the path to the webdriver is correctly set within the code.
* A Google Gemini API key. Replace with your actual API key in the code.

## Usage

1.  Clone or download the Python script.
2.  Install the required libraries.
3.  Replace the placeholder Gemini API key with your own.
4.  Ensure the edge driver path is correct.
5.  Run the script:

    ```bash
    python your_script_name.py
    ```

6.  Follow the voice prompts to interact with the assistant.

## Notes

* This script is designed for Windows environments.
* Voice recognition accuracy may vary depending on microphone quality and ambient noise.
* Ensure a stable internet connection for Gemini API and voice recognition.
* The edge driver path in the code must be updated to the correct location of your webdriver.
