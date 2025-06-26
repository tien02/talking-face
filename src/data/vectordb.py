import uuid
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Configure

class WeviateClient:
    def __init__(self, host: str, port:int, collection_name: str = "Interviewer"):
        self.client = weaviate.connect_to_local(host=host, port=port)
        self.collection_name = collection_name

        if not self.client.collections.exists(collection_name):
            self.client.collections.create(
                name=collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=[
                    wvc.config.Property(name="text", data_type=wvc.config.DataType.TEXT, vectorize_property_name=True),
                    wvc.config.Property(name="speaker_id", data_type=wvc.config.DataType.TEXT, vectorize_property_name=False),
                    wvc.config.Property(name="video_path", data_type=wvc.config.DataType.TEXT, vectorize_property_name=False)
                ]
            )
        
        self.collection = self.client.collections.get(name=collection_name)

    def search(self,
               text: str,
               speaker_id: str,
               alpha: int = 0.5,
               limit: int = 1,
               ) -> list[dict]:
        filters = wvc.query.Filter.by_property("speaker_id").equal(speaker_id)

        results = self.collection.query.hybrid(
            query=text,
            limit=limit,
            alpha=alpha,
            filters=filters,
            return_metadata=wvc.query.MetadataQuery(score=True)
        )

        return [
            {
                "uuid": obj.uuid,
                "score": getattr(obj.metadata, "score", None),
                "distance": getattr(obj.metadata, "distance", None),
                "properties": obj.properties,
                "metadata": obj.metadata
            }
            for obj in results.objects
        ]
        

    def insert(self,
               text:str,
               speaker_id: str,
               video_path: str = "",
               obj_uuid: str | None = None
               ):
        if obj_uuid is None:
            obj_uuid = str(uuid.uuid4())

        self.collection.data.insert(
            uuid=obj_uuid,
            properties={
                "text": text,
                "speaker_id": speaker_id,
                "video_path": video_path
            }
        )
        return obj_uuid
    
    def delete(self, obj_uuid: str) -> bool:
        try:
            self.collection.data.delete_by_id(obj_uuid)
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False
    
    def update(self, obj_uuid: str, updates: dict[str, str]) -> bool:
        try:
            self.collection.data.update(uuid=obj_uuid, properties=updates)
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False

    def get_by_id(self, obj_uuid: str) -> dict:
        try:
            obj = self.collection.query.fetch_object_by_id(obj_uuid)
            return {
                "uuid": obj.uuid,
                "properties": obj.properties
            }
        except Exception:
            return None

    def close(self):
        self.client.close()
