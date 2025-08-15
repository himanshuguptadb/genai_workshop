# Databricks notebook source
# MAGIC %md
# MAGIC # Hands-On Lab: Build Your First Agent with Databricks
# MAGIC
# MAGIC This first agent will follow the workflow of a customer service representative to illustrate the various agent capabilites. 
# MAGIC We'll focus around processing product returns as this gives us a tangible set of steps to follow.
# MAGIC
# MAGIC ## 1 Build Simple Tools
# MAGIC - **SQL Functions**: Create queries that access data critical to steps in the customer service workflow for processing a return.
# MAGIC - **Simple Python Function**: Create and register a Python function to overcome some common limitations of language models.
# MAGIC
# MAGIC ## 2 Integrate with an LLM [AI Playground]
# MAGIC - Combine the tools you created with a Language Model (LLM) in the AI Playground.
# MAGIC
# MAGIC ## 3 Test the Agent [AI Playground]
# MAGIC - Ask the agent a question and observe the response.
# MAGIC - Dive deeper into the agent’s performance by exploring MLflow traces.
# MAGIC

# COMMAND ----------

# MAGIC %run "../00 Setup/00_Config"

# COMMAND ----------

# MAGIC %md
# MAGIC # Customer Service Return Processing Workflow
# MAGIC
# MAGIC Below is a structured outline of the **key steps** a customer service agent would typically follow when **processing a return**. This workflow ensures consistency and clarity across your support team.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 1. Get the Latest Return in the Processing Queue
# MAGIC - **Action**: Identify and retrieve the most recent return request from the ticketing or returns system for a customer.  
# MAGIC - **Why**: Ensures you’re working on the most urgent or next-in-line customer issue.
# MAGIC
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,Get the Latest Return in the Processing Queue
# MAGIC %sql
# MAGIC -- Select the date of the interaction, issue category, issue description, and customer name
# MAGIC SELECT 
# MAGIC   cast(interaction_date as date) as interaction_date, 
# MAGIC   issue_category, 
# MAGIC   issue_description,
# MAGIC   c.name customer_name
# MAGIC FROM cust_service_data s, customer c where s.customer_id = c.customer_id
# MAGIC -- Order the results by the interaction date and time in descending order
# MAGIC ORDER BY interaction_date DESC
# MAGIC -- Limit the results to the most recent interaction
# MAGIC LIMIT 1

# COMMAND ----------

# DBTITLE 1,Create a function registered to Unity Catalog
# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION get_latest_interaction(cust_name STRING)
# MAGIC RETURNS TABLE(interaction_date DATE, issue_category STRING, issue_description STRING, customer_name STRING)
# MAGIC COMMENT 'Returns the most recent customer service interaction for the customer'
# MAGIC RETURN (
# MAGIC   SELECT 
# MAGIC     cast(interaction_date as date) as interaction_date, 
# MAGIC     issue_category, 
# MAGIC     issue_description,
# MAGIC     c.name customer_name
# MAGIC   FROM cust_service_data s
# MAGIC   JOIN customer c ON s.customer_id = c.customer_id
# MAGIC   WHERE lower(c.name) LIKE CONCAT('%', lower(get_latest_interaction.cust_name), '%')
# MAGIC   ORDER BY interaction_date DESC
# MAGIC   LIMIT 1
# MAGIC );

# COMMAND ----------

# DBTITLE 1,Test function call to retrieve latest return
# MAGIC %sql
# MAGIC select * from get_latest_interaction('Nicolas Pelaez')

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## 2. Retrieve Company Policies
# MAGIC - **Action**: Access the internal knowledge base or policy documents related to returns, refunds, and exchanges.  
# MAGIC - **Why**: Verifying you’re in compliance with company guidelines prevents potential errors and conflicts.
# MAGIC
# MAGIC ---

# COMMAND ----------

# MAGIC %sql
# MAGIC select distinct issue_category from cust_service_data

# COMMAND ----------

# DBTITLE 1,Create function to retrieve return policy
# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION get_policy()
# MAGIC RETURNS TABLE (
# MAGIC   policy           STRING,
# MAGIC   policy_details   STRING,
# MAGIC   last_updated     DATE
# MAGIC )
# MAGIC COMMENT 'Returns the details of the Policy based on issue category'
# MAGIC LANGUAGE SQL
# MAGIC RETURN (
# MAGIC   SELECT
# MAGIC     policy,
# MAGIC     policy_details,
# MAGIC     last_updated
# MAGIC   FROM policies
# MAGIC );

# COMMAND ----------

# DBTITLE 1,Test function to retrieve return policy
# MAGIC %sql
# MAGIC select * from get_policy()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## 3. Use the User Name to Look Up the Order History
# MAGIC - **Action**: Query your order management system or customer database using the Username.  
# MAGIC - **Why**: Reviewing past purchases, return patterns, and any specific notes helps you determine appropriate next steps (e.g., confirm eligibility for return).
# MAGIC
# MAGIC ###### Note: We've doing a little trick to give the LLM extra context into the current date by adding todays_date in the function's response
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,Create function that retrieves order history based on userID
# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION get_order_history(cust_name STRING)
# MAGIC RETURNS TABLE (returns_last_12_months INT, issue_category STRING, todays_date DATE)
# MAGIC COMMENT 'This takes the customer name as an input and returns the number of issues and the issue category'
# MAGIC LANGUAGE SQL
# MAGIC RETURN 
# MAGIC SELECT count(*) as issues_last_12_months, issue_category, now() as todays_date
# MAGIC FROM cust_service_data s, customer c where s.customer_id = c.customer_id 
# MAGIC and lower(c.name) like concat('%', lower(get_order_history.cust_name), '%') 
# MAGIC GROUP BY issue_category;

# COMMAND ----------

# DBTITLE 1,Test function that retrieves order history based on userID
# MAGIC %sql
# MAGIC select * from get_order_history('Nicolas Pelaez')
