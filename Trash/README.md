# WebUI Generator with Langgraph and Flask

## Description

This project is a simple web application that generates professional-looking HTML and CSS using AI. It leverages the LangChain framework to create dynamic web content based on user input. The generated HTML and CSS can be previewed and interacted with via a Flask server.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ajitaravind/webuigenerator.git
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

1. **Run the Flask Server**:

   ```bash
   python app.py
   ```

   This will start the Flask server, which listens for POST requests to display the generated HTML and CSS.

2. **Run the Main Script**:

   ```bash
   python main.py
   ```

   This script uses Langgraph to generate HTML and CSS based on user input. The generated content is sent to the Flask server for display.

3. **Interact with the Flask Server**:
   - Navigate to `http://localhost:5000/display` in your web browser to see the generated HTML and CSS.
   - You can also send HTML and CSS code to the server via a POST request to the `/display` endpoint.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
