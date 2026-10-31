"""Exact non-rational quadratic/cubic trimming for cutting-profile export."""
def split(points,t):
 rows=[tuple(points)]
 while len(rows[-1])>1:rows.append(tuple(tuple((1-t)*a[j]+t*b[j] for j in range(2)) for a,b in zip(rows[-1],rows[-1][1:])))
 return tuple(row[0] for row in rows),tuple(row[-1] for row in reversed(rows))

def trim_cubic(points,first,last):
 points=tuple(points)
 if -1e-9<=first<0:first=0.
 if 1<last<=1+1e-9:last=1.
 if len(points)==3:
  a,b,c=points;points=(a,tuple((a[j]+2*b[j])/3 for j in range(2)),tuple((2*b[j]+c[j])/3 for j in range(2)),c)
 if len(points)!=4 or not 0<=first<last<=1:raise ValueError('Expected a quadratic/cubic Bezier interval inside [0,1].')
 if last<1:points=split(points,last)[0]
 if first>0:points=split(points,first/last)[1]
 return points
