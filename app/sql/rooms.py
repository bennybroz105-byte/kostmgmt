# SQL Queries for rooms

GET_AVAILABLE_ROOMS = """
    SELECT 
        r.id,
        r.room_number,
        r.floor,
        r.monthly_rate,
        r.description,
        r.attributes,
        r.created_at,
        r.updated_at
    FROM rooms r
    WHERE r.status = 'available' AND r.realm = $1
    ORDER BY r.room_number;
"""

CREATE_ROOM = """
    INSERT INTO rooms (
        realm, room_number, floor, monthly_rate, description, attributes
    ) VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING id;
"""

UPDATE_ROOM = """
    UPDATE rooms
    SET
        room_number = $1,
        floor = $2,
        monthly_rate = $3,
        description = $4,
        attributes = $5,
        status = $6
    WHERE id = $7 AND realm = $8;
"""

DELETE_ROOM = """
    DELETE FROM rooms WHERE id = $1 AND realm = $2;
"""

# Add more room-related queries as needed