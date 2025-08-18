// MongoDB initialization script for HR Assistant
// This script creates the admin user and database structure

// Switch to admin database
db = db.getSiblingDB('admin');

// Create admin user
try {
    db.createUser({
        user: "admin",
        pwd: "secure_password_change_this",
        roles: [
            {
                role: "userAdminAnyDatabase",
                db: "admin"
            },
            {
                role: "readWriteAnyDatabase",
                db: "admin"
            },
            {
                role: "dbAdminAnyDatabase",
                db: "admin"
            }
        ]
    });
    print("✅ Admin user created successfully");
} catch (e) {
    if (e.code === 11000) {
        print("ℹ️  Admin user already exists");
    } else {
        print("❌ Error creating admin user:", e);
    }
}

// Switch to hr_assistant database
db = db.getSiblingDB('hr_assistant');

// Create collections if they don't exist
try {
    db.createCollection('documents');
    print("✅ Documents collection created");
} catch (e) {
    print("ℹ️  Documents collection might already exist");
}

try {
    db.createCollection('embeddings');
    print("✅ Embeddings collection created");
} catch (e) {
    print("ℹ️  Embeddings collection might already exist");
}

try {
    db.createCollection('cache');
    print("✅ Cache collection created");
} catch (e) {
    print("ℹ️  Cache collection might already exist");
}

// Create indexes for better performance
try {
    db.documents.createIndex({ "metadata.source": 1 });
    db.documents.createIndex({ "metadata.timestamp": 1 });
    print("✅ Document indexes created");
} catch (e) {
    print("ℹ️  Document indexes might already exist");
}

try {
    db.embeddings.createIndex({ "document_id": 1 });
    db.embeddings.createIndex({ "metadata.chunk_index": 1 });
    print("✅ Embedding indexes created");
} catch (e) {
    print("ℹ️  Embedding indexes might already exist");
}

try {
    db.cache.createIndex({ "query_hash": 1 }, { unique: true });
    db.cache.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 1800 });
    print("✅ Cache indexes created with TTL");
} catch (e) {
    print("ℹ️  Cache indexes might already exist");
}

print("🎉 MongoDB initialization completed!");
