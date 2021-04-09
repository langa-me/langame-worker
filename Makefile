PROJECT_ID ?= langame-dev
SERVICE ?= langame-worker

build:
	gcloud builds submit --tag gcr.io/"${PROJECT_ID}"/"$SERVICE"

deploy:
	gcloud run deploy --image gcr.io/"${PROJECT_ID}"/"$SERVICE" --platform managed

delete:
	gcloud run services delete "$SERVICE"
