/**
 * Main entry point for JavaScript sample project.
 */

import { processData } from './utils';
import { DataService } from './services';
import express from 'express';


const app = express();
const PORT = 3000;

function main() {
    console.log('Starting application...');

    const service = new DataService();
    const result = processData(service.getData());

    console.log('Result:', result);
}

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

main();
