# Speculative Ad-hoc Querying

![Version](https://img.shields.io/badge/version-1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Last Updated](https://img.shields.io/badge/last%20updated-2025--03--03-brightgreen)

**SpeQL** is an AI-powered system for **speculative ad-hoc querying**. It enables users to peek immediate results as they are constructing their SQL queries. Please refer to the paper (`./doc/Speculative_Ad-hoc_Querying.pdf`) for more details.

- </span><span style="color: #EA4335;">**To reviewers: The extended figures of the 103 TPCDS queries (Fig. 6 in the submission) are available in the PDF file.**</span>
- The paper is also available on [Arxiv](https://arxiv.org/abs/2503.00714).

## 🏗️ System Architecture

```
┌───────────┐      ┌────────────────┐      ┌────────────┐
│User Editor│◄────►│VSCode Extension│◄────►│SpeQL Server│
└───────────┘      └────────────────┘      └────────────┘
```

The user's input will be first sent to the VSCode extension, then the extension will forward the input to the SpeQL server. The SpeQL server will process the input and return the result to the extension. The extension will then display the result to the user. Please refer to `./doc/demo.mov` for a video demo.

## 📦 TODO: Plug-and-Play Extension

User can easily download the public available extension on VSCode Marketplace that has been connected to the SpeQL server with TPCDS data. We will release the extension once we get the grant. It may take a week or so to release the extension.

**When you are using the extension, we will not record your IP address. And your data will not be used for any purpose. If you have concerns, you may setup your own SpeQL server (see later in this README).**

## 📂 System Breakdown

The code is self-organized into components as follows:

```
1. /plugin --- User editor VSCode extension. Please follow ./plugin/README.md to install it.

2. main.py --- Entry of the SpeQL server. (main_control.py is for control group of 
               the user study and you may ignore it)
     |
     --/src/debug.py --- Speculator logic. Far from optimal and can be improved.
     |       |
     |       --/src/debug_simple.py --- Simple debugging.
     |       |       |
     |       --/src/debug_complex.py --- Complex debugging.
     |       |       |
     |       |       --/src/debug_rule.py --- This is to extract the diff-like 
     |       |                                patch from the input SQL and the 
     |       |                                debugged SQL so that the 
     |       |                                patch can be reapplied to the 
     |       |                                future input SQL.
     |       |
     |       --/src/debug_middle.py --- Autocompletion logic.
     |
     --/src/create.py --- Scheduler logic.
     |       |
     |       --/src/create_rewrite.py --- Rewrite logic that using existing temporary
     |       |                            tables to rewrite the debugged SQL, which
     |       |                            is the most complex part of the system.
     |       |
     |       --/src/create_execute.py --- Issues CREATE TABLE statements to 
     |       |                            the database endpoint.
     |       |
     |       --/src/create_struct.py --- Manages temporary tables.
     |       |
     |       --/src/create_concurrency.py --- Concurrency control logic to support 
     |                                        quality scheduling. E.g., cancel running
     |                                        queries if the user types DOUBLE ENTER 
     |                                        signals.
     |
     --/src/preview.py --- Preview logic. Return immediate results to main.py
     
3. util/ --- Utility functions of the SpeQL server.
     |
     --/util/concurrency.py --- Concurrency control primitives for quality scheduling.
     |
     --/util/cost.py --- Adaptively adjusts the input fetching and LLM invocation
     |                   frequency to save cost.
     |
     |--/util/db_api.py --- Configure and manage DB connections, this version of the
     |                      repository supports Amazon Redshift while others can be
     |                      easily added using their python connectors.
     |
     |--/util/dialect.py --- Dialect-specific SQL patches to support mainstream SQL
     |                       engines.
     |
     |--/util/format.py --- String formatting utilities.
     |
     |--/util/llm_api.py --- LLM API. Now we use OpenAI API, but other LLM providers
     |                       can be easily added.
     |
     |--/util/log.py --- Logging for measurement and debugging.
     |
     |--/util/param.py --- Parameter configuration. Important: you should specify the
     |                     parameters (e.g., --db-host, --api-key, etc.) in the 
     |                     command line before starting the server.
     |
     |--/util/parser.py --- SQL parser based on sqlglot.
     |
     |--/util/prompt.py --- LLM prompts. Far from optimal and can be improved.
     |
     |--/util/sample.py --- Supporting approximate query execution to quickly return
     |                      results even if it is not perfectly accurate. The server 
     |                      will alert the user if the result is sampled.
     |
     |--/util/schema.py --- Schema fetching and management and extracting relevant 
     |                      schema information for the input SQL.
     |
     |--/util/vector_db.py --- Vector database for storing and retrieving schema 
                               information and historical queries.
     
4. vector_db/ --- Historical queries and their embeddings (/vector_db/vector_db.index).

6. test/ --- Test suites and evaluation data. Each text_*.py is a test suite. We 
    |        cannot release user data due to privacy concerns.
    |
    |--/test/plot --- Plotting utilities and figures.
    |
    |--/test/dataset --- Benchmarking evaluation data.
            |
            |--/test/dataset/create_and_query_baseline --- Baseline measurement of 
            |                                              the create and query time on 
            |                                              the TPCDS benchmark.
            |
            |--/test/dataset/debug_line_by_line --- Speculator's debugging trace. That 
            |                                       is, given line-by-line TPCDS 
            |                                       queries, the system's debugging 
            |                                       result.
            |
            |--/test/dataset/create_and_query_line_by_line --- Scheduler's create and 
            |                                              query time on the TPCDS 
            |                                              benchmark with line-by-line 
            |                                              queries.
            |
            |--/test/dataset/tpcds --- TPCDS benchmarking queries.
```

## 🚀 How to Run the System

Here is an example of how to run the system on Amazon Redshift Serverless with minimal effort (assuming you have an AWS account).

### 1️⃣ Subscribe to the TPCDS Data Share
https://aws.amazon.com/marketplace/pp/prodview-iopazp7irqk6s#support

### 2️⃣ Set up Data Shares
Open your query editor (on AWS console), run the following query to see the list of available data shares:

```sql
SELECT share_name, producer_account, producer_namespace
FROM svv_datashares;
```

Use the results from the above query to create a database from the data share. For example:

```sql
CREATE DATABASE tpcds_db FROM DATASHARE tpcds_datashare
OF ACCOUNT 'XXXXXXXXXXX'
NAMESPACE 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX';
```

### 3️⃣ Create External Schemas
```sql
CREATE EXTERNAL SCHEMA ext_tpcds10 FROM REDSHIFT DATABASE tpcds_db SCHEMA tpcds10;
CREATE EXTERNAL SCHEMA ext_tpcds100 FROM REDSHIFT DATABASE tpcds_db SCHEMA tpcds100;
CREATE EXTERNAL SCHEMA ext_tpcds1000 FROM REDSHIFT DATABASE tpcds_db SCHEMA tpcds1000;
```

Set the search path to the external schema:
```sql
set search_path to ext_tpcds10;
-- or
set search_path to ext_tpcds100;
-- or
set search_path to ext_tpcds1000;
```

> **Note**: If you finish querying, you can drop the schema:
> ```sql
> DROP SCHEMA ext_tpcds10;
> DROP SCHEMA ext_tpcds100;
> DROP SCHEMA ext_tpcds1000;
> ```

### 4️⃣ Install SpeQL

```bash
# Python3.10 or higher is required.
apt update
apt install python3-pip

# Install the dependencies
pip install python-Levenshtein redshift_connector snowflake-connector-python sqlglot pandas openai faiss-cpu

# Install Node.js and vsce
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g @vscode/vsce 
sudo npm install -g typescript
sudo npm install vscode node-fetch diff --save
sudo npm install @types/vscode @types/node-fetch @types/diff @types/node --save-dev
sudo npm uninstall @types/vscode
sudo npm dedupe
sudo npm install @types/vscode@1.90.0 --save-dev --force
```

### 5️⃣ Run the SpeQL Server

```bash
python main.py
```

### 6️⃣ Build the Extension

```bash
cd plugin
vsce package
```

### 7️⃣ Install the Extension

1. Press `ctrl+shift+p` (`cmd+shift+p` on mac) to open the command palette.
2. Type "Install from VSIX" and select the vsix file.
3. Select the .vsix file in the plugin folder.
4. Reload VSCode.

Now you can see the SpeQL icon on the bottom right corner of VSCode. Please click it and click "Click me" to enable the SpeQL service.

> ⚠️ **Important Notes**:
> - If you cannot install the .vsix file to your VSCode, please upgrade your VSCode to > 1.90 version.
> - If you don't click "Click me", the SpeQL service will not be enabled.
> - Please refer to ./plugin/README.md for more plugin details.

## 📞 Contact

- Questions on the system please directly email to `lhy@utexas.edu`. The author will check the email on a daily basis and is happy to answer any questions.
- You can also open an issue on the GitHub repository. However, it may take a while to notice the issue and respond.

## 📚 Citation

Cite us: TBD.