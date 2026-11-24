from decimal import Decimal

from boto3.dynamodb.conditions import Key

from models import Alert, Holding


def create_table(dynamodb, name="stockpulse"):
    table = dynamodb.create_table(
        TableName=name,
        KeySchema=[
            {"AttributeName": "partitionKey", "KeyType": "HASH"},
            {"AttributeName": "sortKey", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "partitionKey", "AttributeType": "S"},
            {"AttributeName": "sortKey", "AttributeType": "S"},
            {"AttributeName": "alertIndexKey", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[{
            "IndexName": "alertIndex",
            "KeySchema": [{"AttributeName": "alertIndexKey", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table

def _pk(user_id): # Creates partition key
    return f"USER#{user_id}"


class DynamoStore:
    def __init__(self, table):
        self.table = table

    def _query(self, user_id, prefix):
        resp = self.table.query(
            KeyConditionExpression=Key("partitionKey").eq(_pk(user_id)) & Key("sortKey").begins_with(prefix) # Gets one user's items of one type
        )
        return resp["Items"] 

    def add_watch(self, user_id, code):
        try:
            self.table.put_item(
                Item={"partitionKey": _pk(user_id), "sortKey": f"WATCH#{code}"}, # Creates a new item with the sort key as the code
                ConditionExpression="attribute_not_exists(sortKey)", # Write only if no item with the same sort key exists
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException: # If the item already exists, return False
            return False

    def remove_watch(self, user_id, code):
        resp = self.table.delete_item(
            Key={"partitionKey": _pk(user_id), "sortKey": f"WATCH#{code}"}, # Deletes the item with the sort key as the code
            ReturnValues="ALL_OLD", # Return the old item
        )
        return "Attributes" in resp # Returns True if the item was deleted, False otherwise

    def get_watch(self, user_id): 
        return [item["sortKey"].removeprefix("WATCH#") for item in self._query(user_id, "WATCH#")] # Returns the list of codes

    def save_holding(self, user_id, holding):
        self.table.put_item(Item={ # Creates a new item with the sort key as the code
            "partitionKey": _pk(user_id),
            "sortKey": f"HOLD#{holding.code}", # Creates a new item with the sort key as the code
            "quantity": Decimal(str(holding.quantity)), # Converts the quantity to a decimal
            "avg_cost": Decimal(str(holding.avg_cost)), # Converts the average cost to a decimal
        })

    def _to_holding(self, item):
        return Holding(
            item["sortKey"].removeprefix("HOLD#"),
            int(item["quantity"]),     # Converts the quantity to an integer, so Discord shows "10" not "10.0"
            float(item["avg_cost"]),
        )

    def get_holding(self, user_id, code):
        resp = self.table.get_item(Key={"partitionKey": _pk(user_id), "sortKey": f"HOLD#{code}"})
        item = resp.get("Item") # Missing if the holding doesn't exist
        return self._to_holding(item) if item else None # a Holding, or None

    def remove_holding(self, user_id, code):
        resp = self.table.delete_item(
            Key={"partitionKey": _pk(user_id), "sortKey": f"HOLD#{code}"},
            ReturnValues="ALL_OLD",
        )
        return "Attributes" in resp

    def get_holdings(self, user_id):
        return [self._to_holding(item) for item in self._query(user_id, "HOLD#")]

    def _next_alert_id(self) -> int:
        resp = self.table.update_item(
            Key={"partitionKey": "COUNTER", "sortKey": "ALERT"},
            UpdateExpression="ADD next_id :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(resp["Attributes"]["next_id"])
    
    def add_alert(self, user_id: int, code: str, direction: str, target: float, channel_id: int) -> Alert:
        alert_id = self._next_alert_id()
        alert = Alert(alert_id, user_id, code, direction, target, channel_id)
        self.table.put_item(Item={
            "partitionKey": _pk(user_id),
            "sortKey": f"ALERT#{alert_id}",
            "alertIndexKey": "ALERT",
            "alert_id": alert_id,
            "user_id": user_id,
            "ticker": code,
            "direction": direction,
            "target": Decimal(str(target)),
            "channel_id": channel_id,
        })
        return alert

    def _to_alert(self, item):
        return Alert(
            int(item["alert_id"]),
            int(item["user_id"]),
            item["ticker"],
            item["direction"],
            float(item["target"]),
            int(item["channel_id"]),
        )

    def get_alerts(self, user_id):
        alerts = [self._to_alert(item) for item in self._query(user_id, "ALERT#")] # Gets all the alerts for the user
        alerts.sort(key=lambda alert: alert.alert_id) # Sorts the alerts by alert_id
        return alerts

    def remove_alert(self, user_id, alert_id):
        resp = self.table.delete_item(
            Key={"partitionKey": _pk(user_id), "sortKey": f"ALERT#{alert_id}"}, 
            ReturnValues="ALL_OLD", 
        )
        return "Attributes" in resp

    def get_all_alerts(self):
        resp = self.table.query(
            IndexName="alertIndex",
            KeyConditionExpression=Key("alertIndexKey").eq("ALERT"), # Gets all the alerts
        )
        alerts = [self._to_alert(item) for item in resp["Items"]] # Converts the items to alerts
        alerts.sort(key=lambda alert: alert.alert_id) # Sorts the alerts by alert_id
        return alerts