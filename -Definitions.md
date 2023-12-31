# Definitions
# Table of Contents

1. [Short Suit Points for North](#suppoortPoints)
2. [Predict Opening Bid](#Predict)
1. [Calculate length points for South](#lengthPoints)
2. [Calculate doubleton honor NT downgrade](#Hx)


<a name="supportPoints"></a>
## Calculate Short Suit Points for North (shortSuitPoints)

    v1 = shape(north, any 0xxx) ? 5 : 0  // allow for 2 voids
    v2 = shape(north, any 00xx) ? 5 : 0
    s1 = shape(north, any 1xxx) ? 3 : 0 // allow for 2 singletons
    s2 = shape(north, any 11xx) ? 3 : 0
    d1 = shape(north, any 2xxx) ? 1 : 0 // allow for 3 doubletons
    d2 = shape(north, any 22xx) ? 1 : 0
    d3 = shape(north, any 222x) ? 1 : 0
    shortSuitPoints = v1+v2+s1+s2+d1+d2+d3
    supportPoints = shortSuitPoints + hcp(north)

<a name="Predict"></a>
## Predict Opening Bid

### Calculate length points for South (lengthPoints)<a name="lengthPoints"></a>


    lp1 = spades(south)>4 ? spades(south)-4 : 0
    lp2 = hearts(south)>4 ? hearts(south)-4 : 0
    lp3 = diamonds(south)>4 ? diamonds(south)-4 : 0
    lp4 = clubs(south)>4 ? clubs(south)-4 : 0
    lengthPoints = lp1 + lp2 + lp3 + lp4


### Calculate doubleton honor NT downgrade(s) for South -- 2 cards, 1 honor, not the Ace<a name="Hx"></a>


    S2H = spades(south)==2 and top4(south,spades)==1 and not hascard(south,AS) ? 1 : 0
    H2H = hearts(south)==2 and top4(south,hearts)==1 and not hascard(south,AH) ? 1 : 0
    D2H = diamonds(south)==2 and top4(south,diamonds)==1 and not hascard(south,AD) ? 1 : 0
    C2H = clubs(south)==2 and top4(south,clubs)==1 and not hascard(south,AC) ? 1 : 0
    ntDownGrade = S2H + H2H + D2H + C2H


### Define notrump points for south (ntPoints)

    ntPoints = hcp(south) + lengthPoints - ntDownGrade


### Define suit points for south (suitPoints)


    suitPoints = hcp(south) + lengthPoints


### Define robot notrump shape and exclude any 5 card major

    ntShape = shape(south, any 4333 +any 4432 +any 5332 +any 5422 -5xxx -x5xx)

### Define ntPoint ranges

    oneNT = ntShape and ntPoints>14 and ntPoints<18
    twoNT = ntShape and ntPoints>19 and ntPoints<22
    weakNT = ntShape and ntPoints>10 and ntPoints<15
    overcallNT = ntShape and ntPoints>14 and ntPoints<19  // 15-18

### Define Game Force 2C

    gameForce2C = hcp(south)>22

### Predict South's opening BID

    P1 = gameForce2C
    P2 = P1 or twoNT or oneNT

### Predict South's Opening Suit

    s = spades(south)
    h = hearts(south)
    d = diamonds(south)
    c = clubs(south)
    s1Range = suitPoints>11
    oS = s>4 and s>=h and s>=d and s>=c and s1Range and not P2
    oH = not oS and h>4 and h>=d and h>=c and s1Range and not P2
    oD = not (oS or oH) and ((d>3 and d>=c) or c<3) and s1Range and not P2
    oC = not (oS or oH or oD) and s1Range and not P2
    openingSuit = (oS or oH or oD or oC)
    P3 = P2 or openingSuit

### Define South's Weak 2 Bids

    w2Range = hcp(south)>4 and hcp(south)<12
    weak2S = spades(south)==6 and top5(south,spades)>2 and hcp(south,spades)>4 and hearts(south)<4
    weak2H = hearts(south)==6 and top5(south,hearts)>2 and hcp(south,hearts)>4 and spades(south)<4
    weak2D = diamonds(south)==6 and top5(south,diamonds)>2 and hcp(south,diamonds)>4 and spades(south)<4 and hearts(south)<4
    weakTwo = (weak2S or weak2H or weak2D) and w2Range and not P3
    P4 = P3 or weakTwo

### Define South's loose Weak 2 Bids

    loose2S = spades(south)==6 and top4(south,spades)>1 and w2Range and not P4
    loose2H = hearts(south)==6 and top4(south,hearts)>1 and w2Range and not P4
    loose2D = diamonds(south)==6 and top4(south,diamonds)>1 and w2Range and not P4
    P5 = P4 or (loose2S or loose2H or loose2D)

### Define Preempts

    preempt = shape(south, any 9xxx +any 8xxx +any 7xxx) and hcp(south)<12 and not P4
    P6 = P5 or preempt

### Define Pass

    pass = not P5
    P7 = P6 or pass

### Define opening Major, opening Minor

    oneSpade = oS
    oneHeart = oH
    oneDiamond = oD
    oneClub = oC
    oneMajor = (oS or oH)
    oneMinor = (oC or oD)

P7   // any bid

### Define the short variables for opening bids

    C2x = gameForce2C
    N2x = twoNT
    N1x = oneNT
    S1x = oneSpade
    H1x = oneHeart
    D1x = oneDiamond
    C1x = oneClub
    S2x = weak2S
    H2x = weak2H
    D2x = weak2D
    Sl2 = loose2S
    Hl2 = loose2H
    Dl2 = loose2D
    P3x = preempt
    NBx = pass

### Level responder hand types:

    //and (not x3 or reduce_97_percent )
    //and (not M4 or reduce_97_percent )
    //and (not M3 or reduce_50_percent )
    //and (not x4 or reduce_60_percent )
    //and (not N3 or reduce_75_percent )

### Calculate the Statistics

    action
    average " 1. 2C" 100 * C2x,
    average " 2. 2N" 100 * N2x,
    average " 3. 1N" 100 * N1x,
    average " 4. 1S" 100 * S1x,
    average " 5. 1H" 100 * H1x,
    average " 6. 1D" 100 * D1x,
    average " 7. 1C" 100 * C1x,
    average " 8. 2S" 100 * S2x,
    average " 9. 2H" 100 * H2x,
    average "10. 2D" 100 * D2x,
    average "11. 2s" 100 * Sl2,
    average "12. 2h" 100 * Hl2,
    average "13. 2d" 100 * Dl2,
    average "14. 3x" 100 * P3x,
    average "Pass  " 100 * NBx,


### Define 3+ card Fits for south

    sFit3 = oneSpade and spades(north)>2
    hFit3 = oneHeart and hearts(north)>2

### Define 4+ card fits for south

    sFit4 = oneSpade and spades(north)>3
    hFit4 = oneHeart and hearts(north)>3
    majorFit4 = sFit4 or hFit4

## Define Good, Rebiddable, and Solid Suits
### Define Good suits -- 5+ cards with 2 of the top 3

    gS = spades(south)>4 and top3(south,spades)>1
    gH = hearts(south)>4 and top3(south,hearts)>1
    gD = diamonds(south)>4 and top3(south,diamonds)>1
    gC = clubs(south)>4 and top3(south,clubs)>1

### Define Rebiddable suits -- 5+ cards with 3 of the top 4
### Define Solid suits -- 5 cards with 4 of the top 4 or 6+ cards with 3 of the top 3  

## Define pesky opps e/w distributions and HCP.  We don’t want them mucking up our auctions

    calmEast = shape(east,xxxx -any 8xxx -any 7xxx -any 6xxx -any 55xx)
    calmWest = shape(west,xxxx -any 8xxx -any 7xxx -any 6xxx -any 55xx)
    calmOpps= calmEast and calmWest

## Define South's Weak 2 Bids

    w2Range = hcp(south)>4 and hcp(south)<12
    sW2S = spades(south)==6 and top5(south,spades)>2 and hcp(south,spades)>4 and hearts(south)<4
    sW2H = hearts(south)==6 and top5(south,hearts)>2 and hcp(south,hearts)>4 and spades(south)<4
    sW2D = diamonds(south)==6 and top5(south,diamonds)>2 and hcp(south,diamonds)>4 and spades(south)<4 and hearts(south)<4
    southWeakTwo = (sW2S or sW2H or sW2D) and w2Range
    

## Define East weak 2 bids

    eW2S = spades(east)==6 and top5(east,spades)>2 and hcp(east,spades)>4 and hearts(east)<4 and spades(south)<3 and spades(eWest)<3
    eW2H = hearts(east)==6 and top5(east,hearts)>2 and hcp(east,hearts)>4 and spades(east)<4 and hearts(south)<3 and hearts(eWest)<3
    eW2D = diamonds(east)==6 and top5(east,diamonds)>2 and hcp(east,diamonds)>4 and spades(east)<4 and hearts(east)<4 and diamonds(south)<3
    eastWeakTwo = (eW2S or eW2H or eW2D) and hcp(east)>5 and hcp(east)<10 and shape(east,any 6430 +any 6421 +any 6331 +any 6322)  // should use east's lp rather than hcp


## Calculate the suit ranks for North opener, East overall, and South new suit
### North
#### Predict North's opening suit

    sN = spades(north)
    hN = hearts(north)
    dN = diamonds(north)
    cN = clubs(north)
    nS = sN>4 and sN>=hN and sN>=dN and sN>=cN
    nH = not nS and hN>4 and hN>=dN and hN>=cN
    nD = not nS and not nH and ((dN>3 and dN>=cN))
    nC = not nS and not nH and not nD

#### Calculate North's Rank

    nRS = nS ? 4 : 0
    nRH = nH ? 3 : 0
    nRD = nD ? 2 : 0
    nRC = nC ? 1 : 0
    northRank = nRS+nRH+nRD+nRC   // all except one are zero

### East
#### East's longest suit for overcall

    sE = spades(east)
    hE = hearts(east)
    dE = diamonds(east)
    cE = clubs(east)
    eS = sE>=hE and sE>=dE and sE>=cE
    eH = not eS and hE>=dE and hE>=cE
    eD = not eS and not eH and dE>=cE
eC = not eS and not eH and not eD

#### Calculate East's Rank

    eRS = eS ? 4 : 0
    eRH = eH ? 3 : 0
    eRD = eD ? 2 : 0
    eRC = eC ? 1 : 0
    eastRank = eRS+eRH+eRD+eRC

### South
#### South's longest suit for responding in a new suit at the 2-level

    s = spades(south)
    h = hearts(south)
    d = diamonds(south)
    c = clubs(south)
    sS = s>=h and s>=d and s>=c
    sH = not sS and h>=d and h>=c
    sD = not sS and not sH and d>=c
    sC = not sS and not sH and not sD

#### Calculate South's Rank

    sRS = sS ? 4 : 0
    sRH = sH ? 3 : 0
    sRD = sD ? 2 : 0
    sRC = sC ? 1 : 0
    southRank = sRS + sRH + sRD + sRC

### Requirement for a Free Bid, Negative or Otherwise

    (northRank > eastRank) or (eastRank > southRank)

