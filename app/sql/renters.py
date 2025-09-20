CREATE_RADCHECK_USER = """
    INSERT INTO radcheck (username, attribute, op, value)
    VALUES ($1, 'Cleartext-Password', ':=', $2);
"""

CREATE_RADUSERGROUP_USER = """
    INSERT INTO radusergroup (username, groupname, priority)
    VALUES ($1, 'boarding_tenants', 1);
"""
