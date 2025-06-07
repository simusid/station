from mcp.server import FastMCP
from typing import List, Dict, Any
import sys
import json
STATE="state.json"
TASKS="tasks.json"
EMPLOYEES="employees.json"

mcp = FastMCP("app")

@mcp.tool()
def get_operational_status() -> str:
	"""Return the full operational status of every unit.  This includes the current
	 up to date crew staffing of the ambulances, the location of the ambulances, 
	 their availability marked with the date and time.   """
	with open(STATE) as fh:
		state = fh.read()
	return state

@mcp.tool()
def save_operational_state(**state)-> bool:
	"""Save the full operational status of every unit.  This includes the current
	 up to date crew staffing of the ambulances, the location of the ambulances, 
	 their availability marked with the date and time.  """
	with open(STATE,"w") as fh:
		fh.write(json.dumps(state))
		 
	return True

@mcp.tool()
def get_tasks():
	"""A task is anything we should keep track of until it is resolved.  Examples are
	future license renewals, truck annual inspections, crew reports about problems or
	issues, reminders about future events, or even just notes like 'we should schedule
	a meeting with the police and fire chiefs at some point' """
	with open(TASKS) as fh:
		return fh.read()

@mcp.tool()
def save_tasks(**tasks)->bool:
	"""Save the state of all tasks, reminders, notices, notes, and events"""
	with open(TASKS,"w") as fh:
		fh.write(json.dumps(tasks))
	return True

@mcp.tool()
def get_all_employees():
	"""Return a list of all current employees, their certifcation (EMT Basic or Medic)
	and optional email address"""
	with open (EMPLOYEES) as fh:
		return fh.read()
	
@mcp.tool()
def set_all_employees(**employees):
	"""Save a list of all current employees, with their certification (EMT Basic 
	or Medic) and optional email address"""
	with open(EMPLOYEES,"w") as fh:
		fh.write(json.dumps(employees))
	return True


@mcp.tool()
def get_station_rules()->str:

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
	You should occasionally review all reminders and report which items need attention.
	"""
	return rules

@mcp.resource("config://contacts", description="A list of important contacts at the Station")
def get_station_contacts():
	with open("contacts.json") as fh:
		return fh.read()

 
# run the server
if __name__ == "__main__":
	print('starting server\n', file=sys.stderr)
	mcp.run()