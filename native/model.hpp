#pragma once
#include <cmath>
#include <cstdint>
#ifdef __CUDACC__
#define H3D_HD __host__ __device__
#else
#define H3D_HD
#endif

namespace h3d_native {
enum Kind : uint32_t {Source,Sink,Ipin,Opin,ChanX,ChanY,ChanZ,Sentinel};
struct Cost {float delay,congestion;};
struct ModelHeader {
    char magic[8]={'H','3','D','M','A','P','1','\0'};
    uint32_t version=1,width=0,height=0,layers=0,channels=0,segments=0;
    uint32_t nodes=0,wires=0,reachable=0,groups=0,base_count=0,reserved=0;
    float sink_base=0,sentinel=0;
};
struct ModelNode {
    int32_t xlo,xhi,ylo,yhi,zlo,zhi,adjx,adjy;
    uint32_t kind,dir,segment,cost_index,capacity,reach_begin,reach_count,group_begin,group_count;
};
struct Reach {uint32_t kind,segment,layer;float delay,congestion;};
struct ModelView {
    ModelHeader header;const ModelNode*nodes;const Cost*wires;const Reach*reachable;const uint32_t*groups;
};
H3D_HD inline int absolute(int x){return x<0?-x:x;}
H3D_HD inline float smaller(float a,float b){return a<b?a:b;}
H3D_HD inline Cost wire(const ModelView&m,uint32_t kind,uint32_t seg,uint32_t layer,int dx,int dy,uint32_t to_layer){
    uint64_t index=layer;
    index=index*m.header.layers+to_layer;index=index*m.header.channels+(kind-ChanX);
    index=index*m.header.segments+seg;index=index*m.header.width+uint32_t(dx);index=index*m.header.height+uint32_t(dy);
    return m.wires[index];
}
// Exact non-flat MapLookahead geometry, including native CHANZ direction.
// SOURCE/OPIN adjusted positions and reachable-segment tables come from VPR.
H3D_HD inline float expected(const ModelView&m,uint32_t from,uint32_t to,float criticality,float sink_base){
    const auto&f=m.nodes[from];const auto&t=m.nodes[to];
    if(f.kind==Ipin)return sink_base;
    if(f.kind==Sink)return 0.f;
    int dx,dy;
    if(f.kind!=ChanX && f.kind!=ChanY){dx=absolute(t.adjx-f.adjx);dy=absolute(t.adjy-f.adjy);}
    else{
        int low=f.kind==ChanY?f.ylo:f.xlo,high=f.kind==ChanY?f.yhi:f.xhi;
        int chan=f.kind==ChanY?f.xlo:f.ylo,ts=f.kind==ChanY?t.ylo:t.xlo,tc=f.kind==ChanY?t.xlo:t.ylo;
        int dc=0,orthogonal=0;
        if(tc>chan+1){dc=tc-chan;orthogonal=1;}else if(tc<chan){dc=chan-tc+1;orthogonal=1;}
        int ds=ts>high?ts-high-orthogonal:(ts<low?low-ts-orthogonal:0);
        if((ts<low && f.dir==0) || (ts>high && f.dir==1)){
            int maxseg=int(f.kind==ChanX?m.header.width:m.header.height)-1;
            if(!((low==0&&f.dir==1)||(low==maxseg&&f.dir==0)))++ds;
        }
        dx=absolute(f.kind==ChanY?dc:ds);dy=absolute(f.kind==ChanY?ds:dc);
    }
    Cost c{INFINITY,INFINITY};
    if(f.kind==Source || f.kind==Opin){
        for(uint32_t i=f.reach_begin;i<f.reach_begin+f.reach_count;++i){auto r=m.reachable[i];Cost w{0,0};
            if(r.kind!=Sink && r.kind!=Sentinel)w=wire(m,r.kind,r.segment,r.layer,dx,dy,t.zlo);
            c.delay=smaller(c.delay,r.delay+w.delay);c.congestion=smaller(c.congestion,r.congestion+w.congestion);
        }
    }else{
        uint32_t layer=f.zlo;
        if(f.kind==ChanZ){if(f.dir==0)layer=f.zhi;else if(f.dir==2)layer=t.zlo;}
        c=wire(m,f.kind,f.segment,layer,dx,dy,t.zlo);
    }
    float a=c.delay*criticality,b=c.congestion*(1.f-criticality);return a+b;
}
H3D_HD inline bool inside(const ModelNode&n,const int32_t*b){
    int x=n.dir==1?n.xhi:n.xlo,y=n.dir==1?n.yhi:n.ylo,z=n.dir==1?n.zhi:n.zlo;
    return x>=b[0]&&x<=b[1]&&y>=b[2]&&y<=b[3]&&z>=b[4]&&z<=b[5];
}
}
#undef H3D_HD
