const mongoose = require("mongoose")

const fileSchema = new mongoose.Schema({
    filename : String,
    filepath : String,
    mimetype : String,
    size : Number,
    processedFilename: String,
    uploadDate : {type : Date, default : Date.now()},
})

module.exports = mongoose.model("File", fileSchema);