# Introduction

This Cookbook contains examples and tutorials to help developers build AI systems, offering copy/paste code snippets that you can easily integrate into your own projects.

## About Me

Hi! I'm Dave, AI Engineer and founder of Datalumina®. On my [YouTube channel](https://www.youtube.com/@daveebbelaar?sub_confirmation=1), I share practical tutorials that teach developers how to build AI systems that actually work in the real world. Beyond these tutorials, I also help people start successful freelancing careers. Check out the links below to learn more!

### Explore More Resources

Whether you're a learner, a freelancer, or a business looking for AI expertise, we've got something for you:

1. **Learning Python for AI and Data Science?**  
   Join our **free community, Data Alchemy**, where you'll find resources, tutorials, and support  
   ▶︎ [Learn Python for AI](https://www.skool.com/data-alchemy)

2. **Ready to start or scale your freelancing career?**  
   Learn how to land clients and grow your business  
   ▶︎ [Find freelance projects](https://www.datalumina.com/data-freelancer)

3. **Need expert help on your next project?**  
   Work with me and my team to solve your data and AI challenges  
   ▶︎ [Work with me](https://www.datalumina.com/solutions)

4. **Already building AI applications?**  
   Explore the **GenAI Launchpad**, our production framework for AI systems  
   ▶︎ [Explore the GenAI Launchpad](https://launchpad.datalumina.com/)

## Deploying to Google Cloud Run

The Streamlit Docling knowledge app (`knowledge/docling/5-chat.py`) can be easily deployed to Google Cloud Run for production use. The repository includes a production-ready Dockerfile and deployment configuration.

### Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- Docker installed locally (for testing)
- OpenAI API key

### Building and Deploying

#### 1. Build with Cloud Build

Replace `PROJECT_ID` with your Google Cloud project ID:

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/docling-app
```

#### 2. Deploy to Cloud Run

Replace `PROJECT_ID` and `REGION` with your values, and `YOUR_OPENAI_API_KEY` with your actual API key:

```bash
gcloud run deploy docling-app \
  --image gcr.io/PROJECT_ID/docling-app \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

#### 3. Using Secret Manager (Recommended)

For better security, store your API key in Secret Manager:

```bash
# Create secret
echo "YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-

# Deploy with secret
gcloud run deploy docling-app \
  --image gcr.io/PROJECT_ID/docling-app \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-secrets OPENAI_API_KEY=projects/PROJECT_NUMBER/secrets/openai-api-key:latest
```

### Local Development and Testing

#### Build locally:
```bash
docker build -t docling-app .
```

#### Run locally:
```bash
docker run --rm -e OPENAI_API_KEY=sk-your-key-here -p 8080:8080 docling-app
```

The app will be available at `http://localhost:8080`.

### Resource Configuration

For production workloads, you may need to adjust memory and CPU:

```bash
gcloud run deploy docling-app \
  --image gcr.io/PROJECT_ID/docling-app \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

### Important Considerations

**⚠️ Ephemeral Storage**: Cloud Run containers have ephemeral filesystems. The LanceDB database (`data/lancedb`) and any uploaded files will be reset when the container restarts or when new revisions are deployed.

**For Production**: Consider implementing persistent storage solutions:
- Use external databases (e.g., PostgreSQL with pgvector)
- Mount Google Cloud Storage with gcsfuse
- Use managed vector databases (e.g., Vertex AI Vector Search)
- Implement file uploads to Cloud Storage

**Performance**: The container image is approximately 8.5GB due to ML dependencies. First deployments may take several minutes. Consider using Artifact Registry for faster subsequent deployments in the same region.
