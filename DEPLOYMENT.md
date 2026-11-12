# FinOps Web Deployment Instructions

To host the AI FinOps Optimizer at `https://sarvona.si/ai-agents/finops/`, follow these steps:

## 1. Local Verification
Before deploying, verify the Streamlit app runs locally:
```bash
streamlit run app.py
```

## 2. Prepare Hosting Environment
Choose one of these two recommended methods:

### Option A: Streamlit Community Cloud (Fastest)
1. Push this folder to a Private GitHub repository.
2. Sign in to [Streamlit Cloud](https://share.streamlit.io/).
3. Connect your repo and point the main file to `app.py`.
4. Add your Azure/AWS environment variables in the Streamlit "Secrets" settings.

### Option B: VPS / Docker (Professional)
1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. Deploy to a cloud provider (AWS App Runner or Azure App Service).

## 3. Website Integration (sarvona.si)
To show the tool under your existing page, use an **iFrame** in your website's HTML:

```html
<div class="finops-container">
    <iframe 
        src="https://your-deployed-app-url.streamlit.app/?embed=true"
        frameborder="0"
        width="100%"
        height="900px">
    </iframe>
</div>
```

## 4. Required Dependencies
Ensure your `requirements.txt` contains:
```text
streamlit
pandas
plotly
boto3
azure-identity
azure-mgmt-costmanagement
azure-mgmt-compute
azure-mgmt-resource
```
