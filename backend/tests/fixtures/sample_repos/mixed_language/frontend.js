/**
 * Frontend JavaScript for mixed language project.
 */

import React from 'react';
import axios from 'axios';


async function fetchData() {
    const response = await axios.get('http://localhost:8000/api/data');
    return response.data;
}

function App() {
    const [data, setData] = React.useState([]);

    React.useEffect(() => {
        fetchData().then(setData);
    }, []);

    return React.createElement('div', null, JSON.stringify(data));
}

export default App;
