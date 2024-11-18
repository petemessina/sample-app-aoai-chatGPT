from backend.context.cosmosdb_context import CosmosContext

class DocumentStatusService() :
    def __init__(self, cosmos_context: CosmosContext) -> None:
        self.cosmos_context = cosmos_context