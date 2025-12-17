# Vector Search API

This is a FastAPI-based API for performing semantic vector search on products stored in Firestore, based on the TypeScript logic from `searchCombined.ts`.

## Local Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add your Gemini API key: `GEMINI_API_KEY=your_key_here`
   - Add your Firebase service account JSON as a string: `FIREBASE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}`

3. Ensure your Firestore collection `combined_products` has documents with `embedding` fields (pre-computed embeddings).

## Running Locally

Run the server with uvicorn:
```bash
uvicorn index:app --reload
```

Or using vercel dev:
```bash
vercel dev
```

## Deployment to Vercel

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   vercel
   ```

3. Configure Environment Variables in Vercel Dashboard:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: The complete JSON content of your Firebase service account key (as a string)

**⚠️ Security Note**: Never commit Firebase service account keys to version control. The `.gitignore` and `.vercelignore` files are configured to exclude these files.

The API will be available at `http://localhost:8000`.

## Endpoints

- `GET /`: Health check.
- `GET /search?query=<your_query>`: Perform search and return results as JSON.

Example: `http://localhost:8000/search?query=je%20veux%20une%20assiette%20blanche`

## Notes

- The search uses cosine similarity on pre-computed embeddings.
- Results are limited to 10 items.
- Error handling is included for missing embeddings or API failures.