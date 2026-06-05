import unittest
from calimoto_client import CalimotoClient

class TestCalimotoRouting(unittest.IsolatedAsyncioTestCase):
    def test_decode_polyline_valid(self):
        # 6-decimal precision polyline
        # Decodes to start: (47.800333, 13.045415), end: (47.79438, 13.2877)
        encoded = "y_odzAmif{W~AgQ~Fs\\dt@ybDnAiEpVsfAbVuaApMmf@j@mAnB{@lEM|Eq@tHaKdPwXxFsKfKu[[mNgAeFuJNuBOgGe@sAiAgq@wm@{CqF}EuFoC_FqDcLg@qDH}CgAqPE_G~@uOdBsKj@cBfGsQr@sBzDkLz@aCtD}KjAiGh@cOs@e`@kSgsE_AwKc@qI?mBfBq@`@yCuByCKaCu@{JoBaf@kAw[sDuZgFsCeb@cYwE{EqEaIyEyLeCaJgIaS{FyIgFaIiE_G}MsQ}FoKs]er@eBwFiIcPuC}EcA]gIv@kCtAmFxD{F`FcMhImElEyMzD}Bv@mK`DkPbFgLbC{@N}GfAqFGsG?ic@IwJ~@uo@nZ{Jz@cPS{Og@qF{@w^kN}NsFqEyCsNsDwDBoItCuN`KiDxDgDhCyIpC_RtCoJvFeI`K_U~c@wVri@}CgBgJgIaY}e@_HsHa`@ib@_GyF_BuAke@ad@_M}Lk^aZoAmDiCqBkKmJ_G_R{C{PqBiw@OaF_AsZc@iNQmFs@sUsDmbA{Ecx@e@sHyIqyA[{KYqY\\eb@dCum@VgDzBsVnHkm@bAsJR{Bn@cRc@mUgByRcCoK_k@uvAcAiDuBmHiAcP?mJbAmJnBwHfDkGpDuDrB{@jCy@lFDdFnAfFdEpD|FhGnVxKrl@hNfu@lU~kAzD~IxIrGhEZ`GaA~E}CrDaFdCyGjAuHLmHUcGiAcH}BsIk[g{@aFwTeA{KQiMnBoy@Bqj@cAyTuMkwAqAiMsB{RcMa}@m@cEeFiYcEiWcE}^s@qLF{UlAib@EqQ}@eRoAgLoCePmFsRcRic@qDkM_CeMqG}`@{AaKaLas@aGuWgIaTqp@whAaOaMeNeHeIeEeUcQiQgW_HcMw[ii@s_@wo@mSqa@gZow@aSst@qBaKiCuNsIoj@}BqSoAmN_@sF_A}Pk@wLYiKiDy`A{Am^_B{d@mLk}CeCmq@kDa~@mF}}AWuG{DggAIgSR}Gl@eNt@kMdDkn@RcSs@eQa@aFsDkWmDqNgEmPmB}JeBaJwLml@gz@owDuDkTgEs^yF_bA}AmYcH{fA}Fu_AsI_wAeM_lBmCid@cBmc@oHobCScIqC}bAm@uc@bAosBNsZFwKXcp@_Aa_@oAoPwDaTgAaEcBmG_CwHeH{SiGqUsCcNiD{V_Hax@iEqp@iEcx@u@}M}AuX}Ckm@cBeTwFus@{Dsi@_AeWIcTjAqu@Nij@kC{cA@a[dB}ZtEy\\jEaR~HuU~KqT|K{P|Uo]`h@yu@ri@}t@hE_GLOjFyGjWi[dVqXvFuIp@y@dFmKlB{DxEyMjGyV|DgWrEga@zEq_@tEkUbIaWhiA_qCv_@k_ApGqR`E{OjCwOvCgWzAuUtBeb@`Eij@tBiPvFmWhEqPhw@qqBpUml@xTml@jN}^~Tqg@dl@ggA|F}M`K{[pHo]`Fic@|A_\\Tw]cAq_@oB_XkGoj@aCyQyAyMkJgu@uBqQ{AyL}Fof@}Cy_@Y{XhAoRxCqQpE}QxKqTbYi_@rJeOxGmQrFu[n@qRc@gXmAwOiAeHsHoW}JePqL{LoMqGsE{@yF_AmLVcNxBof@|IyOl@yNm@uPwDiP}HyRoPkOgSaKsUkIm[yEmZiD}k@o@ye@_C}w@iDk]qDsUc\\_tAoLwb@wFcUsAcHyG_^qCw`@w@{^b@}\\xJctAtBaZzAqhAc@il@_@{Me@_PoBqd@mB{k@aFi{AqGgxAa@kLcAkZ_Cal@[wIoAuj@HwIv@oBZoG{AoFoAgAsCoOaF{e@qAeQoAwPoJcoAoHkeAuAya@[qc@?{M`DcqA`Ci\\hKidApRqrBLwAzCsd@pAu\\v@}TdAu^tBco@JqWJuZvAqo@~Aa{@LwF\\spADoNhG_iBxHsiApCsWxCuWfMqz@zB{LdHg_@fN{l@rCmL~E{Q|Ky\\hEgMl^mqA`A{DjNoi@vAkH`Myn@|Hqb@hMir@hSa{@jZqqAtDmS`BaJVqAh@_DfRqlAhC_L|C_SpBiNzGyd@hCoKlA?jC{Ar@uA^_BHwEUgBsBsDSkLfBkOj@eOvTi|AdWcwAnK_c@jiAm~DxVss@tL{Z`Ru]hQkThUmSpOkJt]sNpm@oFvp@oIbZkHdT_MhMiJjOgRlNuV`Wym@vQsb@zTk[fTsUrPyRpPqWhOw\\zMic@pJwg@nMmbAjIm`@v[}aA`Iyb@tCk]hCmiAbEcb@lFoY`Pmh@~FePxFiU`N}v@dGs\\|O_k@hFmSnIeb@|Hws@nKioArIqt@vOi_AbO}q@hSut@j^ubAzVsk@v@gBpTij@fUsx@nLa[tm@qrAdUki@jBsFfPwj@vHs^pM_z@rW_~BvGkg@lO}y@zHeZnJcYfJ{TlHoMxOsTbP_P`RqMra@uYdMwM|ImNrHyQdH{TvBkJjDqUtBcQfAcLfBqStG{t@jDoW`E_TtEaQfPei@hMab@dHkX|C}QdDmc@`@cOYse@kCe^sEc\\yN_x@wEo\\qBmTcC\\sD`HcD~NcC~Ri@nRp@nSl@rMXxFP`DdBhYG`QmBxRaE`b@m@pGo@zHGdJxB`]^bFIlA}BxGwCbDkNjJsQxNoN~PqOaV}IwGoDiGyDse@iDkIiFb@{NfIkH~JkDdKoA|KB~HfFnS`AxIw@fJcHvWsBlD"
        coords = CalimotoClient.decode_polyline(encoded, precision=6)
        
        self.assertEqual(len(coords), 623)
        self.assertAlmostEqual(coords[0][0], 47.800333, places=5)
        self.assertAlmostEqual(coords[0][1], 13.045415, places=5)
        self.assertAlmostEqual(coords[-1][0], 47.79438, places=5)
        self.assertAlmostEqual(coords[-1][1], 13.2877, places=5)

    def test_decode_polyline_empty(self):
        coords = CalimotoClient.decode_polyline("", precision=6)
        self.assertEqual(coords, [])

    def test_decode_polyline_malformed(self):
        # Truncated string that would raise IndexError if bounds were not checked
        encoded_truncated = "y_odzAmif{W~AgQ~Fs"
        coords = CalimotoClient.decode_polyline(encoded_truncated, precision=6)
        self.assertIsInstance(coords, list)

    async def test_get_routing_route_manual(self):
        async with CalimotoClient() as client:
            points = [
                (47.800333, 13.045415),
                (47.794618, 13.287776)
            ]
            decoded = await client.get_routing_route(points=points, routing_profile="motorcycle")
            self.assertGreater(len(decoded), 0)
            self.assertAlmostEqual(decoded[0][0], 47.800333, places=4)
            self.assertAlmostEqual(decoded[0][1], 13.045415, places=4)

    async def test_get_routing_route_url(self):
        async with CalimotoClient() as client:
            url = "https://graphhopper.calimoto.com/routingRoute?point=47.800333,13.045415&point=47.794618,13.287776&device=web"
            decoded = await client.get_routing_route(url=url)
            self.assertGreater(len(decoded), 0)
            self.assertAlmostEqual(decoded[0][0], 47.800333, places=4)
            self.assertAlmostEqual(decoded[0][1], 13.045415, places=4)

if __name__ == '__main__':
    unittest.main()
