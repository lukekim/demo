# Spice.ai Demo App

This is a [Spice.ai](https://spice.ai/) data and AI app.

## Prerequisites

- [Spice.ai CLI](https://docs.spice.ai/get-started/installation) installed
- OpenAI API key
- Hugging Face API token (optional, for LLaMA model)
- `curl` and `jq` for API calls

## Learn More

To learn more about Spice.ai, take a look at the following resources:

- [Spice.ai](https://docs.spice.ai) - learn about Spice.ai features, data, and API.
- [Get started with Spice.ai](https://docs.spice.ai/get-started) - try out the API and make basic queries.

Connect with us on [Discord](https://discord.gg/PUCapX22En) - your feedback is appreciated!

---

## Demo Steps

### Publishing a Spice App in the Cloud

#### Step 1: Forking and Using the Dataset

1. Fork the repository `https://github.com/jeadie/evals` into your GitHub org.

#### Step 2: Creating a New App in the Cloud

1. Log into the [Spice.ai Cloud Platform](https://spice.ai/login) and create a new app called `evals`. The app will start empty.
2. Connect the app to your repository:
   - Go to the **App Settings** tab and select **Connect Repository**.
   - If the repository is not yet linked, follow the prompts to authenticate and link it.

#### Step 3: Deploying the App

1. Set the app to **Public**:
   - Navigate to the app's settings and toggle the visibility to public.
2. Redeploy the app:
   - Click **Redeploy** to load the datasets and configurations from the repository.

#### Step 4: Verifying and Testing

1. Check the datasets in the Spice.ai Cloud:
   - Verify that the datasets are correctly loaded and accessible.
2. Test public access:
   - Log in with a different account to confirm the app is accessible to external users.

---

### Initializing a Local Spice App

1. **Initialize a new local Spice app**

   ```bash
   mkdir demo
   cd demo
   spice init
   ```

2. **Login to Spice.ai Cloud**

   ```bash
   spice login
   ```

3. **Get spicepod from Spicerack**
   Navigate to [spicerack.org](https://spicerack.org), search for `evals`.

   <img width="1679" alt="image" src="https://github.com/user-attachments/assets/248bc281-fbcd-4312-a724-fc295ee0dc13" />

Click on <username>/evals, click on **Use this app**, and copy the `spice connect` command.

   <img width="1679" alt="image" src="https://github.com/user-attachments/assets/ee044042-4a21-4eae-a571-ca9b5c82b976" />
 
 Paste the command into the terminal.
   Navigate to [spicerack.org](https://spicerack.org), search for `evals`, click on <username>/evals, click on **Use this app**, and copy the `spice connect` command. Paste the command into the terminal.

```bash
spice connect <username>/evals
```

The `spicepod.yml` should be updated to:

```yaml
version: v1beta1
kind: Spicepod
name: demo

dependencies:
  - Jeadie/evals
```

5. **Add a model to the spicepod**

   ```yaml
   models:
     - name: gpt-4o
       from: openai:gpt-4o
       params:
         openai_api_key: ${ secrets:SPICE_OPENAI_API_KEY }
   ```

6. **Start spice**

   ```bash
   spice run
   ```

7. **Run an eval**

   ```bash
   curl -XPOST "http://localhost:8090/v1/evals/taxes"      -H "Content-Type: application/json"      -d '{
       "model": "gpt-4o"
     }' | jq
   ```

8. **Explore incorrect results**

   ```bash
   spice sql
   ```

   ```sql
   SELECT
     input,
     output,
     actual
   FROM eval.results
   WHERE value=0.0 LIMIT 5;
   ```

---

### Optional: Create an Eval to Use a Smaller Model

1. Track the outputs of all AI model calls:

   ```yaml
   runtime:
     task_history:
       captured_output: truncated
   ```

2. Define a new view and evaluation:

   ```yaml
   views:
     - name: user_queries
       sql: |
         SELECT
           json_get_json(input, 'messages') AS input,
           json_get_str((captured_output -> 0), 'content') as ideal
         FROM runtime.task_history
         WHERE task='ai_completion'

   evals:
     - name: mimic-user-queries
       description: |
         Evaluates how well a model can copy the exact answers already returned to a user. Useful for testing if a smaller/cheaper model is sufficient.
       dataset: user_queries
       scorers:
         - match
   ```

3. Add a smaller model to the spicepod:

   ```yaml
   models:
     - name: llama3
       from: huggingface:huggingface.co/meta-llama/Llama-3.3-70B-Instruct
       params:
         hf_token: ${ secrets:SPICE_HUGGINGFACE_API_KEY }

     - name: gpt-4o # Keep previous model.
   ```

4. Verify models are loaded:

   ```bash
   spice models
   ```

   You should see both models listed:

   ```shell
   NAME    FROM                                                         STATUS
   gpt-4o  openai:gpt-4o                                                ready
   llama3  huggingface:huggingface.co/meta-llama/Llama-3.3-70B-Instruct ready
   ```

5. Restart the Spice app:

   ```bash
   spice run
   ```

6. Test the larger model or run another eval:

   ```bash
   spice chat
   ```

7. Run evaluations on both models:

   ```bash
   # Run eval with GPT-4
   curl -XPOST "http://localhost:8090/v1/evals/mimic-user-queries" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-4o"}' | jq

   # Run eval with LLaMA
   curl -XPOST "http://localhost:8090/v1/evals/mimic-user-queries" \
     -H "Content-Type: application/json" \
     -d '{"model": "llama3"}' | jq
   ```

8. Compare model performance:

   ```bash
   spice sql
   ```

   ```sql
   WITH model_stats AS (
     SELECT
       model,
       COUNT(*) as total_queries,
       SUM(CASE WHEN value = 1.0 THEN 1 ELSE 0 END) as correct_answers,
       AVG(value) as accuracy,
       AVG(EXTRACT(EPOCH FROM (ended_at - started_at))) as avg_response_time
     FROM eval.results
     WHERE eval = 'mimic-user-queries'
     GROUP BY model
   )
   SELECT
     model,
     total_queries,
     correct_answers,
     ROUND(accuracy * 100, 2) as accuracy_percentage,
     ROUND(avg_response_time, 3) as avg_response_seconds
   FROM model_stats
   ORDER BY accuracy_percentage DESC;
   ```

   This query will show:

   - Total number of queries processed
   - Number of correct answers
   - Accuracy percentage
   - Average response time in seconds

   You can use these metrics to decide if the smaller model provides acceptable performance for your use case.

---

### Full Spicepod Configuration

Include the following `spicepod.yml` for reference:

```yaml
version: v1beta1
kind: Spicepod
name: demo

dependencies:
  - Jeadie/evals

runtime:
  task_history:
    captured_output: truncated

views:
  - name: user_queries
    sql: |
      SELECT
        json_get_json(input, 'messages') AS input,
        json_get_str((captured_output -> 0), 'content') as ideal
      FROM runtime.task_history
      WHERE task='ai_completion'

evals:
  - name: mimic-user-queries
    description: |
      Evaluates how well a model can copy the exact answers already returned to a user. Useful for testing if a smaller/cheaper model is sufficient.
    dataset: user_queries
    scorers:
      - match

models:
  - name: gpt-4o
    from: openai:gpt-4o
    params:
      openai_api_key: ${ secrets:SPICE_OPENAI_API_KEY }

  - name: llama3
    from: huggingface:huggingface.co/meta-llama/Llama-3.3-70B-Instruct
    params:
      hf_token: ${ secrets:SPICE_HUGGINGFACE_API_KEY }
```
