import vt_utils

jp = vt_utils.JourneyPlanner()

brunns_gid = '9021014001760000'
lind_gid = '9021014004490000'
marklands_gid = '9021014004760000'

def test_get_locations():
    brunnsparken = jp.get_locations('Brunnsparken')
    lindholmen = jp.get_locations('Lindholmen')
    marklandsgatan = jp.get_locations('Marklandsgatan')
    return (brunns_gid == brunnsparken[0].get('gid')) and (lind_gid==lindholmen[0].get('gid')) and (marklands_gid==marklandsgatan[0].get('gid'))

def test_get_location_latlong():
    brunnsparken = jp.get_locations('Brunnsparken')
    lindholmen = jp.get_locations('Lindholmen')
    marklandsgatan = jp.get_locations('Marklandsgatan')
    b_lat_long = jp.get_locations_lat_long(brunnsparken[0].get('latitude'), brunnsparken[0].get('longitude'))
    l_lat_long = jp.get_locations_lat_long(lindholmen[0].get('latitude'), lindholmen[0].get('longitude'))
    m_lat_long = jp.get_locations_lat_long(marklandsgatan[0].get('latitude'), marklandsgatan[0].get('longitude'))
    return b_lat_long and m_lat_long and l_lat_long

def test_get_journeys():
    j1 = jp.get_journeys(brunns_gid, lind_gid)
    j2 = jp.get_journeys(lind_gid, marklands_gid)
    j3 = jp.get_journeys(marklands_gid, brunns_gid)
    return (j1.get('results')) and (j2.get('results')) and (j3.get('results'))

def test_get_journey_details():
    j1 = jp.get_journeys(brunns_gid, lind_gid)
    j2 = jp.get_journeys(lind_gid, marklands_gid)
    j3 = jp.get_journeys(marklands_gid, brunns_gid)
    j1_dr = j1.get('results')[0].get('detailsReference')
    j2_dr = j2.get('results')[0].get('detailsReference')
    j3_dr = j3.get('results')[0].get('detailsReference')
    return j1_dr and j2_dr and j3_dr

print('Get locations: Passed ✅' if test_get_locations() else 'Get locations: Failed ❌')
print('Get location latlong: Passed ✅' if test_get_location_latlong() else 'Get location latlong: Failed ❌')
print('Get journeys: Passed ✅' if test_get_journeys() else 'Get journeys: Failed ❌')
print('Get journey details: Passed ✅' if test_get_journey_details() else 'Get journey details: Failed ❌')
