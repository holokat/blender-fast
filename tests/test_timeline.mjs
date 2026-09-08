import assert from 'node:assert/strict';
import {laneAt,median} from '../preview/web/timeline.js';
const events=[
 {lane:'baseline',kind:'lane_start',t:0,phase:'setup'},
 {lane:'baseline',kind:'build_start',t:1,phase:'build'},
 {lane:'baseline',kind:'build_progress',t:2,created:1},
 {lane:'baseline',kind:'render_start',t:3,phase:'first_render'},
 {lane:'baseline',kind:'render_done',t:5,phase:'first_render',seconds:2,image:'/complete.png'},
 {lane:'baseline',kind:'lane_done',t:6,phase:'done',total_seconds:6},
 {lane:'optimized',kind:'build_progress',t:.1,created:64}
];
assert.equal(laneAt(events,'baseline',1.5).created,0);
assert.equal(laneAt(events,'baseline',2.5).created,1);
assert.equal(laneAt(events,'baseline',4.9).image,undefined);
assert.equal(laneAt(events,'baseline',5).image,'/complete.png');
assert.equal(laneAt(events,'baseline',20).elapsed,6);
assert.equal(laneAt(events,'baseline',4).renders.length,0);
assert.equal(laneAt(events,'optimized',2).created,64);
assert.equal(median([3,1,2]),2);assert.equal(median([1,3]),2);assert.equal(median([]),null);
console.log('10 replay timing and isolation checks passed.');
