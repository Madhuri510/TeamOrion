# Team-Orion
# Large Language Models for Knowledge Graph Extraction and Reasoning

This project aims to develop methodologies that integrate Large Language Models (LLMs) with existing biomedical data and unstructured text to create and validate knowledge graphs. These knowledge graphs will facilitate sophisticated reasoning over complex real-world data, enhancing data interpretability and decision-making capabilities. The project will involve building synthetic reference datasets, implementing performance metrics, and developing various systems to manage knowledge graph extraction, querying, and transformation.

# Project Goals
The primary goals of this project are:
* Implement performance metric for question answering based on AI-based knowledge graph extraction.
* Implement LLM-based question answering based on a database containing a knowledge graph.
* Develop approach extracting knowledge graphs from unstructured texts.
* Develop approach to harmonize, merge and query knowledge graphs.
* Develop approach to convert a knowledge graph back to unstructured texts.

# File Structure
The repository is organized into the following folders:

- **Dataset**
  - `raw_abstracts_data.csv` - The raw abstracts extracted from PubMed.
  - `preprocessed_abstracts_data.csv` - The preprocessed abstracts data ready for knowledge graph extraction.

- **Knowledge Graph**
  - `KnowledgeGraph_Final.ipynb` - Notebook for knowledge graph generation.
  - `Test_Abstracts.csv` - Sample abstracts to extract the entities and relations from.
  - `normalized_entities_validation.csv` - The normalized entities extracted from the data.
  - `normalized_relationships_validation.csv` - The normalized relationships extracted from the data.
  - `error_log_validation.txt` - log for missed abstracts or errors occured during extraction.

- **Streamlit App**
  - `app.py` - Streamlit application for visualizing the knowledge graphs and querying data.
  - `Orion_Belt1.jpg` - Supporting image for the app.

# Data Extraction Process
The data extraction process is performed using the notebook `Abstracts Data Extraction.ipynb` in the `Dataset` folder. This notebook:

1. Connects to the PubMed API to retrieve biomedical abstracts.
2. Generates two output files:
   - **raw_abstracts_data.csv**: Contains the raw abstracts data as extracted from PubMed.
   - **preprocessed_abstracts_data.csv**: Contains the cleaned and preprocessed abstracts, ready for further use in knowledge graph generation.

# How to Run
To run the project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/YourUsername/Team-Orion.git
   cd Team-Orion
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama for LLM support:
   - Follow the installation instructions for Ollama: [https://ollama.ai/](https://ollama.ai/)

4. Set the required environment variables:
   ```bash
   export OPENAI_API_KEY=<your-openai-api-key>
   export NEO4J_URI=<your-neo4j-uri>
   export NEO4J_USERNAME=<your-neo4j-username>
   export NEO4J_PASSWORD=<your-neo4j-password>
   ```

5. Run the data extraction notebook:
   - Open `Dataset/Abstracts Data Extraction.ipynb` in Jupyter Notebook or an equivalent IDE.
   - Execute the cells to generate `raw_abstracts_data.csv` and `preprocessed_abstracts_data.csv`.

6. Proceed to the knowledge graph generation:
   - Run the `Knowledge Graph/KnowledgeGraph1.ipynb` notebook.

7. Launch the Streamlit app for visualization:
   ```bash
   streamlit run Streamlit\ App/app.py
   ```

# Contribution
Feel free to fork this repository and submit pull requests. Contributions are welcome!
