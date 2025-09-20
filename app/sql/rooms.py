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
    WHERE r.status = 'available'
    ORDER BY r.room_number;
"""

# Add more room-related queries as needed