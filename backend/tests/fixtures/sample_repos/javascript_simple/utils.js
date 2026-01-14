/**
 * Utility functions for data processing.
 */

import lodash from 'lodash';


export function processData(data) {
    return data.map(item => ({
        ...item,
        processed: true
    }));
}

export function formatDate(date) {
    return date.toISOString();
}

export const CONSTANTS = {
    MAX_SIZE: 1000,
    MIN_SIZE: 10
};
