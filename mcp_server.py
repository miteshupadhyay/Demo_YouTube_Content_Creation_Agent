from mcp.server.fastmcp import FastMCP
from app import get_realtime_info,generate_video_script, generate_video_from_script

mcp = FastMCP("This is for Video Script Generator")

@mcp.tool()
async def get_latest_info_mcp(query):
    return get_realtime_info(query)

@mcp.tool()
async def get_video_script_mcp(query):
    real_info = get_realtime_info(query)
    return generate_video_script(real_info)

@mcp.tool()
async def get_video_from_script_mcp(query):
    real_info = get_realtime_info(query)
    video_script = generate_video_script(real_info)
    return generate_video_from_script(video_script)

if __name__=="__main__":
    mcp.run(transport="stdio")