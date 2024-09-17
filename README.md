Run docker-compose:

```
docker compose up -d
```

Run Queries:

```
docker compose exec -it mongodb mongosh admin -u root -p 'root' --authenticationDatabase admin
>use ms_instance_family_scraper
>db.sku_types.distinct("accelerator")
>db.dropDatabase()
```
