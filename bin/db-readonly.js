// Loaded by db.sh before a read-only session (dev, prod): every write method and write command throws before anything
// is sent. Database and Collection share one prototype each, so db.getSiblingDB() and db.getCollection() are covered.
(() => {
  const stop = (what) => {
    throw new Error(`db.sh: read-only session, ${what} refused. A write needs db.sh prod-write or dev-write, which asks Alfred.`);
  };
  const writesOut = (x) => /"\$(out|merge)"/.test(JSON.stringify(x ?? null));
  const coll = Object.getPrototypeOf(db.getCollection('__db_sh_probe__'));
  for (const m of ['insertOne', 'insertMany', 'insert', 'updateOne', 'updateMany', 'update', 'replaceOne', 'deleteOne',
    'deleteMany', 'remove', 'findOneAndUpdate', 'findOneAndReplace', 'findOneAndDelete', 'findAndModify', 'bulkWrite',
    'initializeOrderedBulkOp', 'initializeUnorderedBulkOp', 'drop', 'createIndex', 'createIndexes', 'ensureIndex',
    'dropIndex', 'dropIndexes', 'renameCollection', 'hideIndex', 'unhideIndex', 'mapReduce', 'reIndex', 'convertToCapped',
    'createSearchIndex', 'createSearchIndexes', 'dropSearchIndex', 'updateSearchIndex']) {
    if (typeof coll[m] === 'function') coll[m] = function () { stop(m); };
  }
  const aggregate = coll.aggregate;
  coll.aggregate = function (...a) {
    if (writesOut(a)) stop('aggregate with $out or $merge');
    return aggregate.apply(this, a);
  };
  const dbp = Object.getPrototypeOf(db);
  for (const m of ['dropDatabase', 'createCollection', 'createView', 'createUser', 'dropUser', 'updateUser',
    'grantRolesToUser', 'revokeRolesFromUser', 'dropAllUsers', 'createRole', 'dropRole', 'setProfilingLevel',
    'shutdownServer', 'fsyncLock', 'fsyncUnlock', 'killOp', 'setLogLevel', 'cloneDatabase', 'copyDatabase']) {
    if (typeof dbp[m] === 'function') dbp[m] = function () { stop(m); };
  }
  const READ = new Set(['ping', 'count', 'distinct', 'find', 'aggregate', 'listCollections', 'listIndexes', 'collStats',
    'dbStats', 'serverStatus', 'buildInfo', 'connectionStatus', 'explain', 'getMore', 'hello', 'isMaster', 'ismaster',
    'dataSize', 'listDatabases', 'getLog', 'top', 'currentOp', 'hostInfo', 'getParameter', 'dbHash']);
  for (const m of ['runCommand', 'adminCommand']) {
    const run = dbp[m];
    dbp[m] = function (cmd, ...rest) {
      const name = typeof cmd === 'string' ? cmd : Object.keys(cmd ?? {})[0];
      if (!READ.has(name)) stop(`${m}(${name})`);
      if (writesOut(cmd)) stop(`${m}(${name}) with $out or $merge`);
      return run.call(this, cmd, ...rest);
    };
  }
})();
