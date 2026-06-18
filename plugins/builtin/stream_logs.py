import os
import re

from plugins.base import PluginBase

class StreamLogsPlugin(PluginBase):
    def __init__(self, **kwargs) -> None:
        super().__init__(downtime=1, **kwargs)

        if not os.path.exists(self.log_file):
            raise FileNotFoundError(f"The file {self.log_file} does not exist.")
        
        self._file = self.log_file.open("r", encoding="utf-8", errors="replace")
        self._file.seek(0, os.SEEK_END)

    def execute(self) -> None:
        line = self._file.readline()
        if not line:
            return

        message = line.rstrip("\n")
        if not message:
            return
        
        formatted_message = self._format_log_line(message)

        for chunk in self._chunk_text(formatted_message):
            self.bot.send_message_to_authenticated_users(chunk)

    def _format_log_line(self, line: str) -> str:
        return re.sub(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}):\d{2},\d+", r"[\1]", line)
    
    def _chunk_text(self, text: str, limit: int = 4000) -> list[str]:
        return [text[i : i + limit] for i in range(0, len(text), limit)] or [text]

    def __del__(self) -> None:
        self._file.close()