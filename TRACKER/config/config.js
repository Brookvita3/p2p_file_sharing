const mongoose = require("mongoose")

const connectDB = async ()=>{
    try {
        await mongoose.connect("mongodb+srv://tranchinhbach:tranchinhbach@co3001.qkb5z.mongodb.net/tracker?retryWrites=true&w=majority&appName=CO3001")
        console.log("MongoDB connected");
    } catch (error) {
        console.log("db connect err: ", error)
    }
}

module.exports = connectDB;