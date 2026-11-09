// Read-only streaming audit of VPR RR XML. No graph mutation or solver.
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <cstdint>
#include <stdexcept>
using namespace std;
string attr(const string&s,const string&k){auto p=s.find(k+"=\"");if(p==string::npos)return "";p+=k.size()+2;return s.substr(p,s.find('"',p)-p);}
uint32_t num(const string&s,const string&k){auto a=attr(s,k);if(a.empty())throw runtime_error("missing "+k);return stoul(a);}
struct Node{uint32_t in=0,out=0;int lo=0,hi=0;bool z=false;string xml;uint32_t outlayers=0,inlayers=0;};
int main(int argc,char**argv){if(argc!=3)return 2;ifstream f(argv[1]);ofstream o(argv[2]);if(!f||!o)return 3;vector<Node> n;string s;uint64_t edges=0,nodes=0,z=0,cross=0;uint32_t xmax=0,ymax=0;
while(getline(f,s)){if(s.find("<node ")!=string::npos){uint32_t id=num(s,"id");if(id>=n.size())n.resize(id+1);auto &v=n[id];v.lo=num(s,"layer_low");v.hi=num(s,"layer_high");v.z=attr(s,"type")=="CHANZ";if(v.z){v.xml=s;z++;}nodes++;xmax=max(xmax,num(s,"xhigh"));ymax=max(ymax,num(s,"yhigh"));}
if(s.find("<edge ")!=string::npos){uint32_t a=num(s,"src_node"),b=num(s,"sink_node");if(a>=n.size()||b>=n.size())throw runtime_error("invalid edge");n[a].out++;n[b].in++;n[a].outlayers|=1u<<n[b].lo;n[a].outlayers|=1u<<n[b].hi;n[b].inlayers|=1u<<n[a].lo;n[b].inlayers|=1u<<n[a].hi;cross+=(n[a].lo!=n[b].lo||n[a].hi!=n[b].hi);edges++;}}
o<<"id\tfanin\tfanout\tinput_layer_mask\toutput_layer_mask\txml\n";uint64_t zero=0,isolated=0;
for(size_t i=0;i<n.size();i++)if(n[i].z&&n[i].in==0){auto&v=n[i];zero++;isolated+=v.out==0;o<<i<<'\t'<<v.in<<'\t'<<v.out<<'\t'<<v.inlayers<<'\t'<<v.outlayers<<'\t'<<v.xml<<'\n';}
cout<<"{\"N\":"<<nodes<<",\"max_id_plus_one\":"<<n.size()<<",\"E\":"<<edges<<",\"CHANZ\":"<<z<<",\"zero_fanin_CHANZ\":"<<zero<<",\"isolated_CHANZ\":"<<isolated<<",\"cross_layer_span_edges\":"<<cross<<",\"xmax\":"<<xmax<<",\"ymax\":"<<ymax<<"}\n";
}

