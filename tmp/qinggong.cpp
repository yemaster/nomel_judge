#include<cstring>
#include<cstdio>
#include<algorithm>
#define fo(i,a,b)for(int i=a,_e=b;i<=_e;i++)
#define fd(i,a,b)for(int i=b,_e=a;i>=_e;i--)
#define ll long long
#define max(a,b)(a>b?a:b)
#define min(a,b)(a<b?a:b)
using namespace std;
const int N=505,mo=1e9+7;
int n,k,w,a[N],v[N],q,x,y,c[N][N];
ll ans,f[N][N];
int main(){
	freopen("qinggong.in","r",stdin);
	freopen("qinggong.out","w",stdout);
	scanf("%d%d%d",&n,&k,&w);
	fo(i,1,k)scanf("%d%d",&a[i],&v[i]);
	scanf("%d",&q);
	fo(i,1,q)scanf("%d%d",&x,&y),c[y][x]++;
	fo(i,-4,k+2000)fo(j,1,n)c[i][j]+=c[i][j-1],f[j][i]=1e18;
	fo(i,1,n)
		fo(j,1,k)if(i>=a[j]&&!(c[j][i]-c[j][i-a[j]]))
			fo(l,1,k)
				f[i][j]=min(f[i][j],f[i-a[j]][l]+v[j]+(j!=l)*w);
	ans=1e18;
	fo(i,1,k)ans=min(ans,f[n][i]);
	printf("%lld",ans<1e18?ans:-1);
}
