from ariadne import QueryType, MutationType, gql, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import FastAPI
import requests
import os

type_defs = gql("""
    type Query {
        attendances: [Attendance!]!
        reservations: [Reservation!]!
        accessLogs: [AccessLog!]!
        transparencyReport(userId: Int!): TransparencyReport!
    }

    type Attendance {
        id: Int!
        user_id: Int!
        timestamp: String!
        is_entry: Boolean!
    }

    type Reservation {
        id: Int!
        user_id: Int!
        menu_id: Int!
        quantity: Int!
    }

    type AccessLog {
        id: Int!
        user_id: Int!
        location: String!
        timestamp: String!
    }

    type TransparencyReport {
        user_id: Int!
        data_used: [String!]!
    }
""")

query = QueryType()
mutation = MutationType()

@query.field("attendances")
async def resolve_attendances(_, info):
    response = requests.get(os.getenv("ATTENDANCE_URL") + "/attendances/")
    return response.json()

@query.field("reservations")
async def resolve_reservations(_, info):
    response = requests.get(os.getenv("CATERING_URL") + "/reservations/")
    return response.json()

@query.field("accessLogs")
async def resolve_access_logs(_, info):
    response = requests.get(os.getenv("ACCESS_CONTROL_URL") + "/access-logs/")
    return response.json()

@query.field("transparencyReport")
async def resolve_transparency_report(_, info, userId: int):
    data_used = []
    if not opt_out_tracking:
        response = requests.get(os.getenv("ATTENDANCE_URL") + f"/attendances/?user_id={userId}")
        if response.json():
            data_used.append("Attendance data")
        response = requests.get(os.getenv("ACCESS_CONTROL_URL") + f"/access-logs/?user_id={userId}")
        if response.json():
            data_used.append("Access logs")
    return {"user_id": userId, "data_used": data_used}

schema = make_executable_schema(type_defs, query, mutation)
graphql_app = GraphQL(schema, debug=True)

app = FastAPI()
app.mount("/", graphql_app)