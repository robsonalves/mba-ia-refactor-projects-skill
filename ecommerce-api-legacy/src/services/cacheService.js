class TtlCache {
    constructor(ttlMs = 1000 * 60 * 15) {
        this.ttlMs = ttlMs;
        this.store = new Map();
    }

    set(key, value) {
        this.store.set(key, { value, expiresAt: Date.now() + this.ttlMs });
    }

    get(key) {
        const entry = this.store.get(key);
        if (!entry) return null;
        if (entry.expiresAt < Date.now()) {
            this.store.delete(key);
            return null;
        }
        return entry.value;
    }
}

const cache = new TtlCache();

module.exports = { cache };
