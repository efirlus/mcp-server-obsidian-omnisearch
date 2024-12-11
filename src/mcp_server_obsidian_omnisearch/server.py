from fastmcp import FastMCP
from urllib.parse import quote
import requests
import os
import logging
import codecs
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up stdout encoding for Windows
if sys.platform == 'win32':
    import msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def serve(obsidian_vault_path: str):
    mcp = FastMCP("obsidian-omnisearch")

    @mcp.tool()
    def obsidian_notes_search(query: str):
        """Search Obsidian(옵시디언) notes and return absolute paths to the matching notes.
        The returned paths can be used with the read_note tool to view the note contents."""
        try:
            search_url: str = "http://localhost:51361/search?q={query}"
            logger.debug(f"Attempting to search with URL: {search_url.format(query=quote(query))}")
            
            response = requests.get(
                search_url.format(query=quote(query)),
                timeout=5  # Add timeout
            )
            response.raise_for_status()
            
            json_response = response.json()
            logger.debug(f"Received response: {json_response}")
            
            sorted_results = sorted(
                json_response, key=lambda x: x["score"], reverse=True
            )
            
            results = [
                f"<title>{item['basename']}</title>\n"
                f"<excerpt>{item['excerpt']}</excerpt>\n"
                f"<score>{item['score']}</score>\n"
                f"<filepath>{os.path.join(obsidian_vault_path, item['path'].lstrip('/'))}</filepath>"
                for item in sorted_results
            ]
            
            logger.debug(f"Returning {len(results)} results")
            return results

        except requests.Timeout:
            logger.error("Request timed out while connecting to Omnisearch")
            return ["Error: Connection to Omnisearch timed out"]
        except requests.RequestException as e:
            logger.error(f"Error connecting to Omnisearch: {str(e)}")
            return [f"Error connecting to Omnisearch: {str(e)}"]
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return [f"Unexpected error: {str(e)}"]

    @mcp.tool()
    def read_note(filepath: str):
        """Read and return the contents of an Obsidian note file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return f"Error reading file: {str(e)}"

    mcp.run()

