class DjangoInternalClient:
    @staticmethod
    def get_internal_demo(token: str):
        return {
            "message": "Django connection check passed",
            "service": "backend",
            "status": "connected",
        }
