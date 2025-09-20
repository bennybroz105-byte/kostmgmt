-- Boarding House Management Schema Extension
-- Extends FreeRADIUS PostgreSQL schema

-- Rooms table to track boarding house rooms
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    room_number VARCHAR(20) NOT NULL,
    floor VARCHAR(10),
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    monthly_rate DECIMAL(10,2) NOT NULL,
    description TEXT,
    attributes JSONB, -- Store flexible room attributes (e.g., AC, furniture, etc)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_room_number UNIQUE(room_number)
);

-- Contract table to store rental agreements
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    contract_number VARCHAR(50) NOT NULL,
    room_id INTEGER NOT NULL,
    tenant_username VARCHAR(64) NOT NULL, -- References radusergroup.username
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_rate DECIMAL(10,2) NOT NULL,
    deposit_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_room FOREIGN KEY(room_id) REFERENCES rooms(id),
    CONSTRAINT fk_tenant FOREIGN KEY(tenant_username) REFERENCES radusergroup(username),
    CONSTRAINT unique_contract_number UNIQUE(contract_number)
);

-- Payments table to track rent payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    payment_number VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64) NOT NULL, -- References manager's username
    CONSTRAINT fk_contract FOREIGN KEY(contract_id) REFERENCES contracts(id),
    CONSTRAINT fk_created_by FOREIGN KEY(created_by) REFERENCES radusergroup(username),
    CONSTRAINT unique_payment_number UNIQUE(payment_number)
);

-- Create indexes for better query performance
CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_contracts_tenant ON contracts(tenant_username);
CREATE INDEX idx_contracts_dates ON contracts(start_date, end_date);
CREATE INDEX idx_payments_contract ON payments(contract_id);
CREATE INDEX idx_payments_date ON payments(payment_date);

-- Insert default user groups into radgroupcheck for role management
INSERT INTO radgroupcheck (groupname, attribute, op, value) VALUES
('boarding_managers', 'Auth-Type', ':=', 'Local'),
('boarding_tenants', 'Auth-Type', ':=', 'Local');

-- Create functions to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_rooms_updated_at
    BEFORE UPDATE ON rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contracts_updated_at
    BEFORE UPDATE ON contracts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();