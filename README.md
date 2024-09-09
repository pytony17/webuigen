# WebUI Generator with Langgraph and Flask

## Description

This project is a simple web application that generates professional-looking HTML and CSS using AI. It leverages the LangChain framework to create dynamic web content based on user input. The generated HTML and CSS can be previewed and modified via text entry / feedback.

Credit to Ajith Aravind whose [project here] (https://github.com/ajitaravind/webuigenerator) was the basis for my project. 

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/pytony17/webuigen.git
   ```

2. Navigate to the project directory:

   ```bash
   cd yourrepository
   ```

3. Rename the `.envsample` file to `.env`:
   ```bash
   mv .envsample .env
   ```

4. Open the `.env` file and add your OpenAI and Tavily API keys:
   ```plaintext
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Flask App**:

   ```bash
   python app.py
   ```

    This will start the Flask application. 
    - Navigate to `http://localhost:5000` and type the description of your web page. 
    - Press Generate and the app will interpret the text and create the web page. 

2. **Interact with the Flask Server**:
   - Press View Result and it will open the web page in a separate browser tab (`http://localhost:5000/display`)
   - View the result and enter your modifications / feedback. 
   - Press Submit Feedback to adjust the web page or press Approved if you are satisfied with the result. 
   - A pop-up windows will indicate when the HTML and CSS code is generated. 
   - Click OK and another pop-up will appear that contains the HTML and CSS code.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
