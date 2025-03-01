const mongoose = require("mongoose");

const fileSchema = new mongoose.Schema({
    filename: String,
    mimetype: String,
    size: Number,
    data: Buffer, // Stores input file as binary data
    processedData: Buffer, // Stores processed file as binary data
    uploadDate: { type: Date, default: Date.now }
});

module.exports = mongoose.model("File", fileSchema);
