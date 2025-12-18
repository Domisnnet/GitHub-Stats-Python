const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();
const db = admin.firestore();

exports.getItems = functions.https.onRequest(async (req, res) => {
  const snapshot = await db.collection("items").get();
  const data = snapshot.docs.map(doc => ({
    id: doc.id,
    ...doc.data()
  }));

  res.json(data);
});