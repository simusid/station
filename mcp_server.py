from mcp.server import FastMCP
from typing import List, Dict, Any
 
import json
TRUCKS = "trucks.json"
ROSTER = "roster.json"
SHIFT = "shift.json"

mcp = FastMCP("app")

@mcp.tool()
def get_truck_status() -> List[Dict[str, Any]]:
	"""Return the status of all ambulances. """
	with open(TRUCKS) as fh:
		trucks = fh.read()
	return trucks

@mcp.tool()
def set_truck_status(trucks: List[Dict[str,Any]])-> bool:
	"""Set the status of all the trucks (ambulances)"""
	with open(TRUCKS,"w") as fh:
		fh.write(json.dumps(trucks))
	return True

@mcp.tool()
def get_roster() -> List[Dict[str, Any]]:
	"""Returns the full roster of employees, their contact info and their EMS certification"""
	with open(ROSTER) as fh:
		return fh.read()
	
@mcp.tool()
def get_dispatch_rules()->str:
	rules="""You must always know the status of all your ambulances. 
	You cannot dispatch an ambulance if it is on a call.
	You cannot dispatch an ambulance if it is out of service.
	If you need to dispatch but both ambulances are unavailable, you must request mutual aid from another town.
	The level of care of an ambulance is either Basic Life Support (BLS) or Advanced
	Life Support (ALS).  
	An ALS response requires at least 1 Paramedic.   If an ambulance is staffed with 
	only EMT Basics, then it is a BLS response.
	Always send an ALS truck to severe calls such as difficulty breathing, chest pain, 
	stroke-like symptoms, significant trauma, and altered mental status.
	If an ALS response is required but only a BLS unit is available.   Send the BLS unit
	while simultaneously requesting mutual aid.
	"""
	return rules

@mcp.tool()
def get_shift_assignments():
	pass


# run the server
if __name__ == "__main__":
	trucks =[{"name":"A1", "status": "in station"},{ "name":"A2","status":"on a call"}]
	with open(TRUCKS,"w") as fh:
		fh.write(json.dumps(trucks))
	mcp.run()