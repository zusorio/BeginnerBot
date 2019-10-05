import json

class Config:
    def __init__(self):
        with open("config.json") as f:
            self.data = json.load(f)
            self.client_id = self.data["client_id"]
            self.client_secret = self.data["client_secret"]
            self.redirect_uri = self.data["redirect_uri"]
            self.start_uri = self.data["start_uri"]
            self.discord_token = self.data["discord_token"]
            self.role_id = self.data["role_id"]
            self.reaction_message_id = self.data["reaction_message_id"]
            self.reaction_message_channel_id = self.data["reaction_message_channel_id"]
            self.guild_id = self.data["guild_id"]
            self.redis_host = self.data["redis_host"]
            self.target_emoji = "✅"
