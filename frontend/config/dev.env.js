let date = require('moment')().format('YYYYMMDD')

// --- OLD CRASHING CODE ---
// let commit = require('child_process').execSync('git rev-parse HEAD').toString().slice(0, 5)

// --- NEW WORKING CODE ---
let commit = "00000" // dummy ID

let version = `"${date}-${commit}"`

console.log(`current version is ${version}`)

module.exports = {
  NODE_ENV: '"development"',
  VERSION: version,
  USE_SENTRY: '0'
}
