export function median(values){if(!values.length)return null;const a=[...values].sort((a,b)=>a-b),i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2}
export function laneAt(events,id,t){
 const result={created:0,calls:0,phase:'setup',elapsed:0,renders:[]};
 for(const event of events||[]){if(event.lane!==id||event.t>t)continue;Object.assign(result,event);if(event.kind==='render_start')result.phaseStart=event.t;if(event.kind==='build_start')result.buildStart=event.t;if(event.kind==='render_done')result.renders.push(event);if(event.kind==='lane_done')result.done=true}
 if(result.kind)result.elapsed=result.done?result.total_seconds:t;
 return result;
}
