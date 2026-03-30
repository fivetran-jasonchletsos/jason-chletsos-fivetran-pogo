pip install -r requirements.txt
cp profiles.yml.example profiles.yml
# Fill in Snowflake credentials in profiles.yml

dbt deps
dbt run
dbt test