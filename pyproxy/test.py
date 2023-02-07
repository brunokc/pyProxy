import old.integration as integration
import json
import xml.etree.ElementTree as ET

xml = '<status version="1.7"><localTime>2022-12-20T16:00:03-07:57</localTime><oat>32</oat><mode>off</mode><cfgem>F</cfgem><cfgtype>heatcool</cfgtype><vacatrunning>off</vacatrunning><filtrlvl>90</filtrlvl><uvlvl>100</uvlvl><humlvl>100</humlvl><ventlvl>100</ventlvl><humid>off</humid><oprstsmsg>idle</oprstsmsg><zones><zone id="1"><name>ZONE 1</name><enabled>on</enabled><currentActivity>manual</currentActivity><rt>68.0</rt><rh>33</rh><fan>off</fan><htsp>66.0</htsp><clsp>70.0</clsp><hold>on</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="2"><name>Zone 2</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="3"><name>Zone 3</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="4"><name>Zone 4</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="5"><name>Zone 5</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="6"><name>Zone 6</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="7"><name>Zone 7</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone><zone id="8"><name>Zone 8</name><enabled>off</enabled><currentActivity>away</currentActivity><rt/><rh>33</rh><fan>off</fan><htsp>60.0</htsp><clsp>80.0</clsp><hold>off</hold><otmr/><zoneconditioning>idle</zoneconditioning><damperposition>15</damperposition></zone></zones></status>'

t = ET.fromstring(xml)
r = integration.handle_status(t)
# z = integration.findnode(t, "/status/zones/zone[@id='1']")
# r = integration.handle_status(z)
print(json.dumps(r, indent=2))