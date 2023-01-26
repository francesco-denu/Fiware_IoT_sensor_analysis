const express = require('express');
const mongoose = require('mongoose');
const app = express();

const cors = require('cors');
app.use(cors());


//Connect to MongoDB and setting strictQuery to false
mongoose.connect('mongodb://mongo-db:27017/orion', { useNewUrlParser: true, useUnifiedTopology: true });



const db = mongoose.connection;
// Print out an error message if there is an error connecting to the database
db.on('error', console.error.bind(console, 'connection error:'));

// Serve static files from the public folder
app.use(express.static('public'));

// Handle GET request to the root endpoint
app.get('/', (req, res) => {
    res.sendFile(__dirname + '/dashboard.html');
});


// Define Mongoose schema and model for the sensor1 collection
const sensor1Schema = new mongoose.Schema({
	id: { type: String, required: true },
  	type: { type: String, required: true },
  	height: {
    	type: { type: String, required: true },
    	value: { type: String, required: true }
  			},
  	heightFlag: {
   		type: { type: String, required: true },
    	value: { type: Number, required: true }
 				 },
  	observedDate: {
    	type: { type: String, required: true },
		value: { type: String, required: true }
  				},
	temperature: {
    	type: { type: String, required: true },
    	value: { type: Number, required: true }
  				},
	temperatureFlag: {
    	type: { type: String, required: true },
    	value: { type: Number, required: true }
  					},
	context: { type: String, required: true }
});

//Sensor1 rappresenta la collezione sensor1 dove sono salvati i valori di temperatura giornalieri 
const Sensor1 = mongoose.model('measurements', sensor1Schema); 


//gestione della GET a /livetemp, dove viene mostrato l'ultimo valore ricevuto dal sensore (e quindi nel database)
app.get('/live_temp', (req, res) => {
Sensor1.findOne({'heightFlag.value': { $ne: -1 } }).sort({'observedDate.value': -1}).exec((error, result) => {
if (error) return console.error(error);
res.json(result);
	});
});



//AVG_TEMP rappresenta la collezione averagetemp che contiene 24 elementi che rappresentano i valori di temperatura media 
const AVG_TEMP = mongoose.model('means', sensor1Schema);

// /avg_temp che ritorna tutti i valori nella collezione averagetemp con i valori medi 
app.get('/avg_temp', (req, res) => {
    AVG_TEMP.find({}).sort({'observedDate.value': 1}).limit(24).exec((error, result) => {
        if (error) return console.error(error);
        res.json(result);
    });
});



const moment = require('moment');
//trovo la data YYYY-MM-DD dell'ultimo valore nel database ricevuto dai sensori
app.get('/recent_date', (req, res) => { 
    Sensor1.findOne().sort({ "observedDate.value": -1 }).limit(1).exec((err, data) => {
        if (err) throw err;
        if (!data) {
            res.status(404).json({ error: "No data found" });
            return;
        }
        // Use the moment.utc() function to create a moment object in UTC time
        const recentDate = moment.utc(data.observedDate.value).format("YYYY-MM-DD");
        res.json({date: recentDate});
    });
});




//fissata la data date posso trovare tutti i valori di quel giorno
app.get('/date/:date', (req, res) => {
    const date = req.params.date;
    const startOfDay = moment.utc(`${date}T00:00:00Z`, 'YYYY-MM-DDTHH:mm:ssZ').startOf('day').toISOString();
    const endOfDay = moment.utc(`${date}T23:59:59Z`, 'YYYY-MM-DDTHH:mm:ssZ').endOf('day').toISOString();

    Sensor1.find({
        "observedDate.value": {
            $gte: startOfDay,
            $lt: endOfDay
        }
    }).sort({ "observedDate.value": 1 }).exec((error, result) => {
        if (error) return console.error(error);
        res.json(result);
    });
});



app.listen(3000, () => {
    console.log('Server started on http://localhost:3000');
});





