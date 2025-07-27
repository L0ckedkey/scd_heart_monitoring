from google.cloud.sql.connector import Connector
import sqlalchemy

connector = Connector()

def getconn():
    conn = connector.connect(
        "flowing-encoder-406115:asia-southeast2:scd-instance-1",
        "pymysql",
        user="scd",
        password="scd2023",
        db="scd"
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

with pool.connect() as db_conn:
#    print(pool.connect())
    res = db_conn.execute(sqlalchemy.text("SELECT * FROM patients;")).fetchall()
      # commit transactions
#    db_conn.commit()
    for i in res:
        print(i)
    
