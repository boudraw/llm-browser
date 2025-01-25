from typing import List
from pymongo import MongoClient
from bson import ObjectId
from itertools import combinations


def get_tags_context():
    return """Analyze the text and provide a list of Tags and Entities found in the text.
Include at least 3 different tags.

Example:
- Input: "Devin is the latest achievement in AI. It is a complete AI software engineer."

- Output:
```json
{
    "tags": ["AI", "Devin", "software engineer"],
}
```


Important:
- Never include 'undefined', 'null' or similar in the list of tags.
"""


mongodb_client = None


class TagMemory:
    def __init__(self, host: str = 'mongodb://127.0.0.1:27017'):
        global mongodb_client
        if not mongodb_client and host:
            mongodb_client = MongoClient(host)
        if not mongodb_client:
            raise ValueError("MongoDB host is required at least once.")
        # Connect to MongoDB
        self.db = mongodb_client.memory

    def __del__(self):
        global mongodb_client
        # Clean up and close connections
        if mongodb_client:
            mongodb_client.close()

    def insert_tags_relations(self, tags: List[str]):
        # Generate all combinations of two tags
        tag_pairs = list(combinations(tags, 2))

        # Insert each pair into the database
        for tag_from, tag_to in tag_pairs:
            self.db.tag_relations.insert_one({"tag_from": tag_from, "tag_to": tag_to})

    def query_tag_relation_count(self, tag: str):
        # Query to find count of related tags
        pipeline = [
            {"$match": {"$or": [{"tag_from": tag}, {"tag_to": tag}]}},
            {"$group": {"_id": {"$cond": [{"$eq": ["$tag_from", tag]}, "$tag_to", "$tag_from"]}, "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "tag": "$_id", "count": 1}}
        ]

        result = list(self.db.tag_relations.aggregate(pipeline))

        # Convert the result to a dictionary
        tag_counts = {item['tag']: item['count'] for item in result if item['tag'] != tag}

        return tag_counts
