/**
 * Service classes for data management.
 */

import axios from 'axios';
import { processData } from './utils';


export class DataService {
    constructor() {
        this.data = [];
    }

    getData() {
        return this.data;
    }

    async fetchFromAPI(url) {
        const response = await axios.get(url);
        return processData(response.data);
    }

    saveData(newData) {
        this.data.push(newData);
    }
}

export class CacheService {
    constructor() {
        this.cache = new Map();
    }

    get(key) {
        return this.cache.get(key);
    }

    set(key, value) {
        this.cache.set(key, value);
    }
}
